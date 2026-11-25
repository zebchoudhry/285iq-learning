"""
Load hand-written question banks (see learning/services/question_bank.py for the format).

    py manage.py load_written_questions --subject biology --dry-run
    py manage.py load_written_questions --subject biology --markdown review.md   (readable review copy)
    py manage.py load_written_questions --subject biology                        (load into the database)
    py manage.py load_written_questions --subject biology --retire-filler        (also switch off the
                                                                                  generic repeated filler)

Nothing is loaded if any question fails validation or any lesson can't be found. Questions
already in a lesson (same wording) are skipped, so running it twice is safe.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count

from learning.generators.base import create_question_from_dict
from learning.models import Lesson, Question
from learning.services import question_bank

FILLER_MIN_LESSONS = 20  # a question repeated in this many lessons is filler, not lesson content


class Command(BaseCommand):
    help = "Load hand-written questions from question_bank/<subject>/*.txt"

    def add_arguments(self, parser):
        parser.add_argument("--subject", "-s", required=True, help="Subject folder, e.g. biology")
        parser.add_argument("--dir", default=None, help="Override the folder to read")
        parser.add_argument("--dry-run", action="store_true", help="Validate and report only")
        parser.add_argument("--markdown", default=None, help="Write a readable review document to this path")
        parser.add_argument("--inactive", action="store_true", help="Load the questions switched off")
        parser.add_argument("--retire-filler", action="store_true",
                            help="Switch off questions repeated across many lessons (generic filler)")
        parser.add_argument("--min-lessons", type=int, default=FILLER_MIN_LESSONS,
                            help=f"With --retire-filler: wording in at least this many lessons counts as filler "
                                 f"(default {FILLER_MIN_LESSONS})")

    def handle(self, *args, **opts):
        subject = opts["subject"].strip().lower()
        directory = Path(opts["dir"]) if opts["dir"] else Path(settings.BASE_DIR) / "question_bank" / subject
        if not directory.is_dir():
            raise CommandError(f"No folder at {directory}")
        parsed = question_bank.parse_directory(directory)
        if parsed.errors:
            for e in parsed.errors[:40]:
                self.stderr.write(self.style.ERROR(e))
            raise CommandError(f"{len(parsed.errors)} problem(s) found. Nothing loaded.")
        if opts["markdown"]:
            Path(opts["markdown"]).write_text(
                question_bank.review_markdown(parsed.questions, f"{subject.capitalize()} question review"),
                encoding="utf-8")
            self.stdout.write(f"Review document written to {opts['markdown']}")

        grouped = question_bank.lessons_in(parsed.questions)
        missing, plan = [], []
        for (topic, title), questions in grouped.items():
            lesson = Lesson.objects.filter(
                topic__subject__name__iexact=subject, topic__name__iexact=topic, title__iexact=title,
                topic__is_active=True, is_active=True).first()
            if lesson is None:
                missing.append(f"{topic} / {title}")
            else:
                plan.append((lesson, questions))
        if missing:
            for m in missing:
                self.stderr.write(self.style.ERROR(f"No such lesson: {m}"))
            raise CommandError("Fix the lesson names above. Nothing loaded.")

        total = sum(len(qs) for _, qs in plan)
        self.stdout.write(f"{len(parsed.questions)} questions are valid across {len(plan)} lessons.")
        if opts["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"[dry run] would load {total} questions"))
            if opts["retire_filler"]:
                self.stdout.write(f"[dry run] would switch off {self._filler(subject, opts['min_lessons']).count()} filler questions")
            return

        created = skipped = 0
        with transaction.atomic():
            for lesson, questions in plan:
                for q in questions:
                    d = q.as_dict(f"{question_bank.SOURCE_PREFIX} ({subject})")
                    question, was_created = create_question_from_dict(lesson, d, skip_duplicates=True)
                    if was_created:
                        created += 1
                        if opts["inactive"]:
                            Question.objects.filter(pk=question.pk).update(is_active=False)
                    else:
                        skipped += 1
            retired = 0
            if opts["retire_filler"]:
                retired = self._filler(subject, opts["min_lessons"]).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(
            f"Loaded {created} questions ({skipped} already there)"
            + (f"; switched off {retired} filler questions" if opts["retire_filler"] else "") + "."))

    def _filler(self, subject, min_lessons=FILLER_MIN_LESSONS):
        """Active, non-written questions in this subject whose wording appears in many lessons."""
        subject_lessons = Question.objects.filter(is_active=True, lesson__topic__subject__name__iexact=subject)
        repeated = (
            subject_lessons.exclude(source__startswith=question_bank.SOURCE_PREFIX)
            .values("question_text")
            .annotate(n=Count("lesson_id", distinct=True))
            .filter(n__gte=max(int(min_lessons), 2))
            .values_list("question_text", flat=True)
        )
        return subject_lessons.filter(question_text__in=list(repeated)).exclude(
            source__startswith=question_bank.SOURCE_PREFIX)
