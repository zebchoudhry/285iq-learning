"""
Load structured lesson content for Physics Energy topic.
Content uses format supported by formatLessonContent() in lessons.html:
Key Concept, Formula/Key Info, Worked Example, Common Mistake, Quick Check.

Usage: python manage.py load_energy_content [--lesson "Energy Stores & Systems"] [--dry-run]

Idempotent and safe to run multiple times.
"""
from django.core.management.base import BaseCommand, CommandError
from learning.models import Subject, Topic, Lesson
from learning.data.energy_lessons_content import ENERGY_LESSON_CONTENT, ENERGY_LESSON_SKILLS


def _short_title(full_title):
    """Derive short title from '1.1 - Energy Stores & Systems' -> 'Energy Stores & Systems'."""
    if not full_title or " - " not in full_title:
        return full_title.strip()
    return full_title.split(" - ", 1)[1].strip()


class Command(BaseCommand):
    help = "Load structured content for Physics Energy topic lessons"

    def add_arguments(self, parser):
        parser.add_argument(
            "--lesson",
            type=str,
            default=None,
            help="Target a single lesson by short title (e.g. 'Energy Stores & Systems')",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Log what would be updated without saving",
        )

    def handle(self, *args, **options):
        lesson_filter = options.get("lesson")
        dry_run = options.get("dry_run", False)

        # 1. Find Physics subject
        subject = Subject.objects.filter(name__iexact="physics", is_active=True).first()
        if not subject:
            raise CommandError("Physics subject not found. Run bootstrap_gcse or seed_physics_subtopics first.")

        # 2. Find Energy topic
        topic = Topic.objects.filter(
            subject=subject,
            name="Energy",
            is_active=True,
        ).first()
        if not topic:
            raise CommandError("Energy topic not found under Physics.")

        # 3. Safety Guard
        lesson_count = topic.lessons.filter(is_active=True).count()
        if lesson_count < 10:
            raise CommandError(
                "Energy topic structure looks unexpected (expected >= 10 lessons). Aborting."
            )

        # 4. Process lessons
        lessons = topic.lessons.filter(is_active=True).order_by("order")
        updated = 0
        skipped = 0

        for lesson in lessons:
            short = _short_title(lesson.title)
            if lesson_filter and short != lesson_filter:
                continue
            content = ENERGY_LESSON_CONTENT.get(short)
            if not content:
                skipped += 1
                if lesson_filter:
                    self.stderr.write(self.style.WARNING(f"No content defined for: {lesson_filter}"))
                continue
            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Would update: {lesson.title}"))
                updated += 1
                continue
            lesson.content = content
            lesson.key_skills = ENERGY_LESSON_SKILLS.get(short, [])
            lesson.save(update_fields=["content", "key_skills"])
            updated += 1
            self.stdout.write(self.style.SUCCESS(f"Updated: {lesson.title}"))

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Lessons updated: {updated}"))
        if not lesson_filter:
            self.stdout.write(f"Skipped (no content defined): {skipped}")
