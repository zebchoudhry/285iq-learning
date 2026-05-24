"""
Generate flashcards from Lesson.key_skills and Question content.
Usage: python manage.py generate_flashcards [--topic-id ID] [--dry-run]
Targets ~5-10 cards per topic for MVP; avoids duplicates by normalizing front text.
"""
import re

from django.core.management.base import BaseCommand

from learning.models import Topic, Flashcard, Lesson, Question


def _normalize_front(text):
    """Normalize front text for duplicate detection."""
    if not text:
        return ""
    s = re.sub(r"\s+", " ", text.strip().lower())
    return s[:200]


class Command(BaseCommand):
    help = "Generate flashcards from key_skills and questions (~5-10 per topic)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--topic-id",
            type=int,
            default=None,
            help="Limit to a single topic ID (optional)",
        )
        parser.add_argument(
            "--max-per-topic",
            type=int,
            default=10,
            help="Max flashcards per topic (default: 10)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be created without saving",
        )

    def handle(self, *args, **options):
        topic_id = options.get("topic_id")
        max_per_topic = max(1, options.get("max_per_topic", 10))
        dry_run = options.get("dry_run", False)

        topics = Topic.objects.filter(is_active=True).select_related("subject")
        if topic_id:
            topics = topics.filter(id=topic_id)

        if not topics.exists():
            self.stderr.write(self.style.WARNING("No topics found."))
            return

        total_created = 0
        total_skipped = 0

        for topic in topics:
            created, skipped = self._generate_for_topic(
                topic, max_per_topic, dry_run
            )
            total_created += created
            total_skipped += skipped

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would create {total_created} flashcards, "
                    f"skip {total_skipped} duplicates"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {total_created} flashcards, skipped {total_skipped} duplicates"
                )
            )

    def _generate_for_topic(self, topic, max_per_topic, dry_run):
        existing_fronts = set()
        for fc in Flashcard.objects.filter(topic=topic, is_active=True):
            existing_fronts.add(_normalize_front(fc.front))

        created = 0
        skipped = 0
        order = 0

        # From Lesson.key_skills: skill -> "Key concept from {topic}"
        for lesson in Lesson.objects.filter(
            topic=topic, is_active=True
        ).order_by("order"):
            skills = lesson.key_skills or []
            for skill in skills:
                if isinstance(skill, str) and skill.strip():
                    front = skill.strip()[:500]
                    back = f"Key concept: {skill.strip()}"
                    if created + skipped >= max_per_topic:
                        break
                    norm = _normalize_front(front)
                    if norm and norm not in existing_fronts:
                        if not dry_run:
                            Flashcard.objects.create(
                                topic=topic,
                                front=front,
                                back=back,
                                order=order,
                                is_active=True,
                            )
                            order += 1
                        created += 1
                        existing_fronts.add(norm)
                    else:
                        skipped += 1
            if created + skipped >= max_per_topic:
                break

        # From Questions: question_text -> correct_answer or explanation
        for q in Question.objects.filter(
            lesson__topic=topic, is_active=True
        ).select_related("lesson").order_by("lesson__order", "difficulty_level"):
            if created + skipped >= max_per_topic:
                break
            front = (q.question_text or "").strip()[:500]
            back = (q.correct_answer or q.explanation or "").strip()[:1000]
            if not front or not back:
                continue
            norm = _normalize_front(front)
            if norm in existing_fronts:
                skipped += 1
                continue
            if not dry_run:
                Flashcard.objects.create(
                    topic=topic,
                    front=front,
                    back=back,
                    order=order,
                    is_active=True,
                )
                order += 1
            created += 1
            existing_fronts.add(norm)

        return created, skipped
