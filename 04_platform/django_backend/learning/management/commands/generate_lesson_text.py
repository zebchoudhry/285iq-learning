"""
Generate/refresh lesson text using configured LLM backend.
Usage: python manage.py generate_lesson_text [--lesson-id ID] [--only-empty] [--dry-run]
"""
from django.core.management.base import BaseCommand

from learning.models import Lesson
from learning.services.llm_service import generate as llm_generate


class Command(BaseCommand):
    help = "Generate lesson text content from topic metadata"

    def add_arguments(self, parser):
        parser.add_argument("--lesson-id", type=int, default=None, help="Optional single lesson to update")
        parser.add_argument("--only-empty", action="store_true", help="Only fill empty lesson content")
        parser.add_argument("--dry-run", action="store_true", help="Preview without saving")

    def handle(self, *args, **options):
        lesson_id = options.get("lesson_id")
        only_empty = options.get("only_empty", False)
        dry_run = options.get("dry_run", False)

        lessons = Lesson.objects.filter(is_active=True).select_related("topic__subject")
        if lesson_id:
            lessons = lessons.filter(id=lesson_id)
        if only_empty:
            lessons = lessons.filter(content__exact="")

        updated = 0
        for lesson in lessons:
            prompt = (
                f"Write concise GCSE lesson notes for {lesson.topic.subject.display_name} - {lesson.topic.name}. "
                f"Lesson title: {lesson.title}. Include key definitions, method steps, and one worked example."
            )
            try:
                text = llm_generate(prompt=prompt, max_tokens=700, temperature=0.2)
            except Exception:
                continue
            if not text:
                continue
            if not dry_run:
                lesson.content = text.strip()
                lesson.save(update_fields=["content"])
            updated += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"{prefix}Updated {updated} lesson content record(s)."))
