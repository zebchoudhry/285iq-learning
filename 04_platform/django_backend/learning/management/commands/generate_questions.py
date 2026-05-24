"""
Generate questions for a subject using template-based generators.
Usage: python manage.py generate_questions --subject mathematics [--per-lesson 10] [--output data/questions_mathematics.json]
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from learning.models import Lesson
from learning.generators.base import resolve_lesson, create_question_from_dict

SUBJECT_GENERATORS = {
    "mathematics": "learning.generators.maths",
    "physics": "learning.generators.physics",
    "biology": "learning.generators.biology",
    "chemistry": "learning.generators.chemistry",
}


def _get_generator(subject_slug):
    """Return the generate function for the subject."""
    mod_path = SUBJECT_GENERATORS.get(subject_slug.lower())
    if not mod_path:
        return None
    import importlib
    mod = importlib.import_module(mod_path)
    return getattr(mod, "generate", None)


class Command(BaseCommand):
    help = "Generate questions for a subject and optionally save to JSON or load into DB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject",
            "-s",
            type=str,
            required=True,
            choices=["mathematics", "physics", "biology", "chemistry"],
            help="Subject to generate questions for",
        )
        parser.add_argument(
            "--per-lesson",
            "-n",
            type=int,
            default=10,
            help="Number of questions to generate per lesson (default: 10)",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default=None,
            help="Optional path to save JSON file (if omitted, loads directly into DB)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report what would be generated, do not save or load",
        )

    def handle(self, *args, **options):
        subject_slug = options["subject"].lower()
        per_lesson = max(1, options["per_lesson"])
        output_path = Path(options["output"]) if options.get("output") else None
        dry_run = options.get("dry_run", False)

        gen_fn = _get_generator(subject_slug)
        if not gen_fn:
            self.stderr.write(self.style.ERROR(f"Unknown subject: {subject_slug}"))
            return

        # Map slug to subject name in DB (load commands use Mathematics, Physics, etc.)
        subject_names = {
            "mathematics": "Mathematics",
            "physics": "Physics",
            "biology": "Biology",
            "chemistry": "Chemistry",
        }
        subject_name = subject_names[subject_slug]

        lessons = Lesson.objects.filter(
            topic__subject__name__iexact=subject_name,
            topic__subject__is_active=True,
            topic__is_active=True,
            is_active=True,
        ).select_related("topic").order_by("topic__order", "order")

        if not lessons.exists():
            self.stderr.write(
                self.style.WARNING(
                    f"No lessons found for {subject_name}. Run load_{subject_slug}_lessons first."
                )
            )
            return

        blocks = []
        total_questions = 0
        for lesson in lessons:
            topic_name = lesson.topic.name
            lesson_title = lesson.title
            questions = gen_fn(topic_name, lesson_title, per_lesson)
            if not questions:
                continue
            block = {
                "subject": subject_name,
                "topic": topic_name,
                "lesson": lesson_title,
                "questions": questions,
            }
            blocks.append(block)
            total_questions += len(questions)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would generate {total_questions} questions "
                    f"across {len(blocks)} lessons for {subject_name}"
                )
            )
            return

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if len(blocks) == 1:
                data = blocks[0]
            else:
                data = blocks
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Saved {total_questions} questions to {output_path}"
                )
            )
            return

        # Load directly into DB
        created = 0
        skipped = 0
        for block in blocks:
            _, _, lesson_obj = resolve_lesson(
                block["subject"], block["topic"], block["lesson"]
            )
            if not lesson_obj:
                continue
            for q in block["questions"]:
                _, was_created = create_question_from_dict(
                    lesson_obj, q, skip_duplicates=True
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded: {created} created, {skipped} skipped (duplicates)"
            )
        )
