"""
Merge duplicate GCSE subjects into canonical naming convention.

Canonical: GCSE Physics, GCSE Maths, GCSE Chemistry, GCSE Biology
Handles: Physics/GCSE Physics, Mathematics/GCSE Maths, Chemistry/GCSE Chemistry,
         Biology/GCSE Biology, and GSCE Physics typo.

Usage:
  python manage.py merge_duplicate_subjects --dry-run
  python manage.py merge_duplicate_subjects
  python manage.py merge_duplicate_subjects --verbose
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from learning.models import (
    Subject,
    Topic,
    Lesson,
    Question,
    Flashcard,
    StudySession,
    StudentExamSettings,
    StudentExamDate,
)
from users.models import StudentTopicPerformance
from dashboard.models import MockExam, PastPaper, NotificationLog


# Canonical display_name per subject key
CANONICAL_DISPLAY = {
    'physics': 'GCSE Physics',
    'mathematics': 'GCSE Maths',
    'chemistry': 'GCSE Chemistry',
    'biology': 'GCSE Biology',
}


def get_subject_key(subject):
    """Map subject to normalized key (physics, mathematics, chemistry, biology) or None."""
    name = (subject.name or '').strip().lower()
    display = (subject.display_name or '').strip().lower()
    combined = f"{name} {display}"

    if 'physic' in combined:
        return 'physics'
    if 'math' in combined or 'mathematic' in combined:
        return 'mathematics'
    if 'chem' in combined:
        return 'chemistry'
    if 'bio' in combined:
        return 'biology'
    return None


def choose_canonical(subjects, key):
    """
    Pick canonical subject from list.
    Prefer: display_name == "GCSE X", then most questions, then first by id.
    """
    canonical_name = CANONICAL_DISPLAY.get(key, key.title())
    # Prefer exact match to canonical display_name (including GSCE typo for physics)
    for s in subjects:
        dn = (s.display_name or '').strip()
        if dn == canonical_name:
            return s
        if key == 'physics' and dn == 'GSCE Physics':
            return s

    # Else prefer subject with most questions (via topics -> lessons -> questions)
    best = None
    best_count = -1
    for s in subjects:
        qty = Question.objects.filter(
            lesson__topic__subject=s,
            is_active=True
        ).count()
        if qty > best_count:
            best_count = qty
            best = s
    return best if best else subjects[0]


class Command(BaseCommand):
    help = "Merge duplicate GCSE subjects into canonical GCSE Physics, GCSE Maths, GCSE Chemistry, GCSE Biology"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Report changes without applying')
        parser.add_argument('--verbose', action='store_true', help='Detailed logging')

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be applied"))
            self.stdout.write("")

        # Group subjects by key
        subjects_by_key = {}
        for s in Subject.objects.filter(is_active=True).select_related('exam_board'):
            key = get_subject_key(s)
            if key is None:
                if self.verbose:
                    self.stdout.write(f"  Skip (non-core): {s.display_name} (id={s.id})")
                continue
            if key not in subjects_by_key:
                subjects_by_key[key] = []
            subjects_by_key[key].append(s)

        # Process each key
        merged = []
        for key, subjects in subjects_by_key.items():
            if len(subjects) < 2:
                # Fix GSCE typo if single subject
                if len(subjects) == 1:
                    s = subjects[0]
                    if (s.display_name or '').strip() == 'GSCE Physics':
                        if not self.dry_run:
                            s.display_name = 'GCSE Physics'
                            s.save()
                        merged.append((key, s, [], "Fixed GSCE typo"))
                continue

            canonical = choose_canonical(subjects, key)
            non_canonical = [s for s in subjects if s.id != canonical.id]
            canonical.display_name = CANONICAL_DISPLAY.get(key, key.title())
            if (canonical.display_name or '').strip() == 'GSCE Physics':
                canonical.display_name = 'GCSE Physics'

            if not self.dry_run:
                canonical.save()
                for nc in non_canonical:
                    self._merge_subject_into(nc, canonical)

            merged.append((key, canonical, non_canonical, "Merged"))

        # Output summary
        self._print_final_summary()

    def _merge_subject_into(self, non_canonical, canonical):
        """Merge non_canonical subject into canonical. Handles topic name conflicts."""
        with transaction.atomic():
            # 3a. Topics
            for topic in Topic.objects.filter(subject=non_canonical):
                existing = Topic.objects.filter(subject=canonical, name=topic.name).first()
                if existing is None:
                    topic.subject = canonical
                    topic.save()
                    if self.verbose:
                        self.stdout.write(f"    Moved topic: {topic.name}")
                else:
                    # Merge: move lessons, flashcards, and all topic FKs to existing
                    Lesson.objects.filter(topic=topic).update(topic=existing)
                    Flashcard.objects.filter(topic=topic).update(topic=existing)
                    from learning.models import StudentGymState, TopicStrengthSnapshot
                    # StudentGymState: unique (student, topic) - keep canonical, delete dup
                    for sgs in StudentGymState.objects.filter(topic=topic):
                        if StudentGymState.objects.filter(student=sgs.student, topic=existing).exists():
                            sgs.delete()
                        else:
                            sgs.topic = existing
                            sgs.save()
                    # TopicStrengthSnapshot: unique (student, topic, date) - keep canonical, delete dup
                    for tss in TopicStrengthSnapshot.objects.filter(topic=topic):
                        if TopicStrengthSnapshot.objects.filter(
                            student=tss.student, topic=existing, date=tss.date
                        ).exists():
                            tss.delete()
                        else:
                            tss.topic = existing
                            tss.save()
                    # StudentTopicPerformance: unique (student, topic) - merge stats, delete dup
                    for stp in StudentTopicPerformance.objects.filter(topic=topic):
                        other = StudentTopicPerformance.objects.filter(
                            student=stp.student, topic=existing
                        ).first()
                        if other:
                            other.questions_attempted += stp.questions_attempted
                            other.questions_correct += stp.questions_correct
                            other.time_spent_seconds += stp.time_spent_seconds
                            if stp.last_interaction and (
                                not other.last_interaction or stp.last_interaction > other.last_interaction
                            ):
                                other.last_interaction = stp.last_interaction
                            other.save()
                            stp.delete()
                        else:
                            stp.topic = existing
                            stp.save()
                    StudySession.objects.filter(topic=topic).update(topic=existing)
                    topic.delete()
                    if self.verbose:
                        self.stdout.write(f"    Merged topic into existing: {existing.name}")

            # 3b. Subject FKs
            StudySession.objects.filter(subject=non_canonical).update(subject=canonical)

            # StudentExamSettings: merge duplicates
            for ses in StudentExamSettings.objects.filter(subject=non_canonical):
                if StudentExamSettings.objects.filter(student=ses.student, subject=canonical).exists():
                    ses.delete()
                else:
                    ses.subject = canonical
                    ses.save()

            # StudentExamDate: merge duplicates
            for sed in StudentExamDate.objects.filter(subject=non_canonical):
                if StudentExamDate.objects.filter(
                    student=sed.student,
                    subject=canonical,
                    paper_label=sed.paper_label,
                ).exists():
                    sed.delete()
                else:
                    sed.subject = canonical
                    sed.save()

            MockExam.objects.filter(subject=non_canonical).update(subject=canonical)

            # PastPaper: unique (subject, exam_board, year, paper_number) - merge duplicates
            for pp in PastPaper.objects.filter(subject=non_canonical):
                if PastPaper.objects.filter(
                    subject=canonical,
                    exam_board=pp.exam_board,
                    year=pp.year,
                    paper_number=pp.paper_number,
                ).exists():
                    pp.delete()
                else:
                    pp.subject = canonical
                    pp.save()

            NotificationLog.objects.filter(subject=non_canonical).update(subject=canonical)

            non_canonical.delete()

    def _print_final_summary(self):
        """Output final subject list, question counts, topic counts."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Final Subject Summary ==="))
        self.stdout.write("")

        for s in Subject.objects.filter(is_active=True).order_by('display_name'):
            q_count = Question.objects.filter(
                lesson__topic__subject=s,
                is_active=True,
            ).count()
            t_count = Topic.objects.filter(subject=s).count()
            self.stdout.write(
                f"  {s.display_name}: {q_count} questions, {t_count} topics"
            )

        # Verify no orphans
        orphan_topics = Topic.objects.filter(subject__isnull=True).count()
        if orphan_topics:
            self.stdout.write(self.style.ERROR(f"  WARNING: {orphan_topics} orphan topics"))
        else:
            self.stdout.write("")
            self.stdout.write("  No orphan topics.")
