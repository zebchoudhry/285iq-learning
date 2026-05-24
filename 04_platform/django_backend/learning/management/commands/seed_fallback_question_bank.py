"""
Ensure a minimum fallback question set per topic.
Usage: python manage.py seed_fallback_question_bank [--min-per-topic 6] [--dry-run]
"""
from django.core.management.base import BaseCommand

from learning.models import Lesson, Question, Topic


class Command(BaseCommand):
    help = "Seed fallback questions for topics with low question counts"

    def add_arguments(self, parser):
        parser.add_argument("--min-per-topic", type=int, default=6, help="Minimum active questions per topic")
        parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")

    def handle(self, *args, **options):
        min_per_topic = max(1, int(options.get("min_per_topic", 6)))
        dry_run = options.get("dry_run", False)

        created = 0
        for topic in Topic.objects.filter(is_active=True).select_related("subject"):
            count = Question.objects.filter(lesson__topic=topic, is_active=True).count()
            if count >= min_per_topic:
                continue

            lesson = (
                Lesson.objects.filter(topic=topic, is_active=True)
                .order_by("order")
                .first()
            )
            if lesson is None:
                if not dry_run:
                    lesson = Lesson.objects.create(
                        topic=topic,
                        title="Fallback Practice",
                        content=f"Starter fallback questions for {topic.name}.",
                        estimated_duration=15,
                        lesson_type="practice",
                        difficulty_level=2,
                        key_skills=[],
                        order=999,
                        is_active=True,
                    )
                else:
                    # virtual placeholder for dry run output logic
                    lesson = None

            needed = min_per_topic - count
            for i in range(needed):
                if not dry_run:
                    Question.objects.create(
                        lesson=lesson,
                        question_text=f"[Fallback] {topic.name}: practice question {i + 1}",
                        correct_answer="Sample answer",
                        explanation="Fallback bank question used when generated content is unavailable.",
                        question_type="short_answer",
                        difficulty_level=2,
                        marks_available=1,
                        source="fallback_bank",
                        is_active=True,
                    )
                created += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"{prefix}Created {created} fallback question(s)."))
