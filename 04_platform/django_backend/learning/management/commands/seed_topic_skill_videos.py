from django.core.management.base import BaseCommand

from learning.models import Lesson, SkillVideo, Topic


class Command(BaseCommand):
    help = "Create one active SkillVideo per topic from existing lesson video URLs."

    def add_arguments(self, parser):
        parser.add_argument("--subject", help="Optional subject name filter, e.g. mathematics.")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        subject_filter = (options.get("subject") or "").strip()
        dry_run = options["dry_run"]

        topics = Topic.objects.filter(is_active=True, subject__is_active=True).select_related("subject")
        if subject_filter:
            topics = topics.filter(subject__name__iexact=subject_filter)

        created = 0
        skipped = 0
        updated = 0

        for topic in topics.order_by("subject__display_name", "order", "name"):
            if SkillVideo.objects.filter(topic=topic, is_active=True).exists():
                skipped += 1
                continue

            lesson = (
                Lesson.objects.filter(topic=topic, is_active=True)
                .exclude(video_url="")
                .order_by("order", "id")
                .first()
            )
            if not lesson:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"No lesson video found for {topic.subject.display_name} / {topic.name}"))
                continue

            title = f"{topic.name}: quick revision fix"
            defaults = {
                "title": title,
                "subject": topic.subject,
                "topic": topic,
                "tier": getattr(topic.subject, "tier", "both") or "both",
                "duration_seconds": 120,
                "video_url": lesson.video_url,
                "intervention_goal": f"Review the core method for {topic.name}.",
                "is_active": True,
            }

            if dry_run:
                created += 1
                self.stdout.write(f"[DRY RUN] Would create: {topic.subject.display_name} / {title}")
                continue

            _, was_created = SkillVideo.objects.update_or_create(
                subject=topic.subject,
                topic=topic,
                title=title,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        label = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{label}Topic videos created: {created}, updated: {updated}, skipped: {skipped}"
            )
        )
