"""
Add questions from the template engine (learning/generators/engine.py) to
lessons that have templates.

Each question is generated fresh with new numbers, so nothing is copied from
past papers or other sites.

Examples:
    py manage.py generate_templated_questions --dry-run
    py manage.py generate_templated_questions --subject mathematics --fill-below 12 --per-lesson 12
    py manage.py generate_templated_questions --seed 7
"""
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from learning.generators.base import create_question_from_dict
from learning.generators.engine import SOURCE_PREFIX, generate_for_lesson, question_key, templates_for
from learning.models import Lesson, Question


class Command(BaseCommand):
    help = "Add template-generated questions (fresh numbers each time) to lessons that have templates."

    def add_arguments(self, parser):
        parser.add_argument("--subject", "-s", default="", help="Only this subject (e.g. mathematics)")
        parser.add_argument("--per-lesson", "-n", type=int, default=12,
                            help="New questions to add to each lesson (default 12)")
        parser.add_argument("--fill-below", type=int, default=0,
                            help="Only top up lessons that have fewer than this many questions")
        parser.add_argument("--seed", type=int, default=None,
                            help="Random seed, for repeatable output")
        parser.add_argument("--dry-run", action="store_true", help="Report only, save nothing")

    def handle(self, *args, **opts):
        rng = random.Random(opts["seed"])
        per_lesson = max(1, opts["per_lesson"])
        subject_filter = (opts["subject"] or "").strip().lower()

        lessons = (
            Lesson.objects.filter(is_active=True, topic__is_active=True, topic__subject__is_active=True)
            .select_related("topic__subject")
            .annotate(n_questions=Count("questions"))
            .order_by("topic__subject__name", "topic__order", "order")
        )
        if subject_filter:
            lessons = lessons.filter(topic__subject__name__iexact=subject_filter)
        if opts["fill_below"]:
            lessons = lessons.filter(n_questions__lt=opts["fill_below"])

        total_new = lessons_touched = 0
        for lesson in lessons:
            subject, topic = lesson.topic.subject.name, lesson.topic.name
            if not templates_for(subject, topic, lesson.title):
                continue
            existing = {
                question_key(text, answer)
                for text, answer in Question.objects.filter(lesson=lesson)
                .values_list("question_text", "correct_answer")
            }
            questions = generate_for_lesson(subject, topic, lesson.title, per_lesson, rng, existing)
            if not questions:
                continue
            lessons_touched += 1
            if opts["dry_run"]:
                total_new += len(questions)
                self.stdout.write(f"  {subject} / {lesson.title}: +{len(questions)} (has {lesson.n_questions})")
                continue
            created = 0
            with transaction.atomic():
                for q in questions:
                    # Duplicates were already ruled out on (wording, answer); multiple-choice
                    # questions can share wording and differ only in their options.
                    _, was_created = create_question_from_dict(lesson, q, skip_duplicates=False)
                    created += int(was_created)
            total_new += created
            self.stdout.write(f"  {subject} / {lesson.title}: +{created} (had {lesson.n_questions})")

        verb = "Would add" if opts["dry_run"] else "Added"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {total_new} questions across {lessons_touched} lessons "
            f"(source tag: '{SOURCE_PREFIX}<template code>')."
        ))
