"""
Backfill QuestionStep and SkillNode so practice can use weakness-first selection.
Uses topic + subject to infer one skill per question; creates QuestionStep(step_order=1).

Usage:
  python manage.py backfill_question_skills
  python manage.py backfill_question_skills --dry-run
  python manage.py backfill_question_skills --subject mathematics
"""
import re
from django.core.management.base import BaseCommand

from learning.models import Question, QuestionStep, SkillNode


def _subject_prefix(subject_name):
    """Map subject display name to skill code prefix."""
    if not subject_name:
        return "GEN"
    name = (subject_name or "").strip().lower()
    if "math" in name:
        return "MATH"
    if "phys" in name:
        return "PHY"
    if "bio" in name:
        return "BIO"
    if "chem" in name:
        return "CHEM"
    return "GEN"


def _topic_to_slug(topic_name):
    """Normalize topic name to a short slug for skill code."""
    if not topic_name:
        return "TOPIC"
    s = re.sub(r"[^\w\s-]", "", (topic_name or "").strip())
    s = re.sub(r"[-\s]+", "_", s).upper()
    return (s[:36] or "TOPIC").strip("_")


def get_or_create_skill_for_topic(subject_display_name, topic_name):
    """Get or create a SkillNode for this subject+topic. Returns (SkillNode, created)."""
    prefix = _subject_prefix(subject_display_name)
    slug = _topic_to_slug(topic_name)
    code = f"{prefix}_{slug}" if slug != "TOPIC" else f"{prefix}_TOPIC"
    if len(code) > 50:
        code = code[:50]
    subject_label = (subject_display_name or "General")[:100]
    description = f"GCSE {subject_label} - {topic_name or 'General'}"
    skill, created = SkillNode.objects.get_or_create(
        code=code,
        defaults={
            "subject": subject_label,
            "description": description[:500] if description else "",
            "difficulty_weight": 1.0,
        },
    )
    return skill, created


class Command(BaseCommand):
    help = "Backfill QuestionStep and SkillNode from question topic so weakness-first practice works"

    def _print_final_report(self):
        """Output total questions, steps, coverage, and skill count."""
        total_questions = Question.objects.count()
        total_steps = QuestionStep.objects.count()
        questions_with_steps = Question.objects.filter(steps__isnull=False).distinct().count()
        coverage = (questions_with_steps / total_questions * 100) if total_questions else 100
        skill_count = SkillNode.objects.count()
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Final Report ==="))
        self.stdout.write(f"  Total Questions: {total_questions}")
        self.stdout.write(f"  Total QuestionSteps: {total_steps}")
        self.stdout.write(f"  Coverage: {coverage:.1f}%")
        self.stdout.write(f"  Unique SkillNodes: {skill_count}")

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be done without creating records",
        )
        parser.add_argument(
            "--subject",
            type=str,
            default=None,
            help="Limit to subject name (e.g. mathematics, Physics)",
        )
        parser.add_argument(
            "--batch",
            type=int,
            default=2000,
            help="Max questions to process per run (default 2000). Use 0 for no limit.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        subject_filter = (options.get("subject") or "").strip() or None
        batch = options.get("batch", 2000)

        # Questions that have no steps yet
        ids_with_steps = set(
            QuestionStep.objects.values_list("question_id", flat=True).distinct()
        )
        qs = (
            Question.objects.filter(is_active=True)
            .exclude(id__in=ids_with_steps)
            .select_related("lesson", "lesson__topic", "lesson__topic__subject")
        )
        if subject_filter:
            qs = qs.filter(lesson__topic__subject__name__iexact=subject_filter)
        if batch > 0:
            qs = qs[:batch]

        total = qs.count()
        if total == 0:
            self.stdout.write(
                self.style.SUCCESS("No questions without steps found. Nothing to do.")
            )
            self._print_final_report()
            return

        self.stdout.write(
            f"Found {total} question(s) without steps. {'[DRY RUN]' if dry_run else 'Backfilling...'}"
        )

        skills_created = 0
        steps_created = 0
        seen_codes = set()

        for question in qs:
            try:
                topic = question.lesson.topic
                subject = topic.subject
                subject_name = getattr(subject, "display_name", None) or getattr(
                    subject, "name", ""
                )
                topic_name = topic.name
            except Exception:
                continue

            if dry_run:
                code = f"{_subject_prefix(subject_name)}_{_topic_to_slug(topic_name)}"
                if len(code) > 50:
                    code = code[:50]
                if code not in seen_codes:
                    seen_codes.add(code)
                    skills_created += 1
                steps_created += 1
                continue

            skill, skill_created = get_or_create_skill_for_topic(
                subject_name, topic_name
            )
            if skill_created and skill.code not in seen_codes:
                seen_codes.add(skill.code)
                skills_created += 1

            QuestionStep.objects.get_or_create(
                question=question,
                step_order=1,
                defaults={
                    "skill": skill,
                    "hint_level_1": (question.explanation or "")[:500],
                },
            )
            steps_created += 1

            if steps_created % 500 == 0 and steps_created > 0:
                self.stdout.write(f"  Processed {steps_created} questions...")

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would create {steps_created} QuestionSteps and up to {len(seen_codes)} SkillNodes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {steps_created} QuestionSteps. New SkillNodes: {skills_created}."
                )
            )

        self._print_final_report()
