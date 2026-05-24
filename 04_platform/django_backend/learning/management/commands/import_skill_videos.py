import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from learning.models import SkillNode, SkillVideo, Subject, Topic


class Command(BaseCommand):
    help = "Import short intervention videos from a CSV file."

    REQUIRED_COLUMNS = {"title", "subject", "topic", "video_url"}

    def add_arguments(self, parser):
        parser.add_argument("--file", "-f", required=True, help="CSV file to import.")
        parser.add_argument("--dry-run", action="store_true", help="Validate without writing.")

    def handle(self, *args, **options):
        path = Path(options["file"])
        dry_run = options["dry_run"]
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
            return

        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = self.REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                self.stderr.write(self.style.ERROR(f"Missing required columns: {', '.join(sorted(missing))}"))
                return

            created = 0
            updated = 0
            skipped = 0
            errors = 0

            for row_number, row in enumerate(reader, start=2):
                title = (row.get("title") or "").strip()
                video_url = (row.get("video_url") or "").strip()
                subject_name = (row.get("subject") or "").strip()
                topic_name = (row.get("topic") or "").strip()
                if not title or not video_url or not subject_name or not topic_name:
                    self.stderr.write(self.style.WARNING(f"Row {row_number}: missing title/subject/topic/video_url"))
                    errors += 1
                    continue

                subject = Subject.objects.filter(name__iexact=subject_name).first()
                if not subject:
                    subject = Subject.objects.filter(display_name__icontains=subject_name).first()
                if not subject:
                    self.stderr.write(self.style.WARNING(f"Row {row_number}: subject not found: {subject_name}"))
                    errors += 1
                    continue

                topic = Topic.objects.filter(subject=subject, name__iexact=topic_name).first()
                if not topic:
                    topic = Topic.objects.filter(subject=subject, name__icontains=topic_name).first()
                if not topic:
                    self.stderr.write(self.style.WARNING(f"Row {row_number}: topic not found: {topic_name}"))
                    errors += 1
                    continue

                skill = None
                skill_code = (row.get("skill_code") or "").strip()
                if skill_code:
                    skill, _ = SkillNode.objects.get_or_create(
                        code=skill_code,
                        defaults={
                            "subject": subject.display_name,
                            "description": (row.get("intervention_goal") or "").strip(),
                            "difficulty_weight": 1.0,
                        },
                    )

                defaults = {
                    "subject": subject,
                    "topic": topic,
                    "skill": skill,
                    "exam_board": (row.get("exam_board") or "").strip(),
                    "tier": self._clean_tier(row.get("tier")),
                    "duration_seconds": self._clean_duration(row.get("duration_seconds")),
                    "thumbnail_url": (row.get("thumbnail_url") or "").strip(),
                    "intervention_goal": (row.get("intervention_goal") or "").strip(),
                    "is_active": self._clean_bool(row.get("is_active"), default=True),
                }

                if dry_run:
                    exists = SkillVideo.objects.filter(video_url=video_url).exists()
                    updated += 1 if exists else 0
                    created += 0 if exists else 1
                    continue

                _, was_created = SkillVideo.objects.update_or_create(
                    video_url=video_url,
                    defaults={"title": title, **defaults},
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

            label = "[DRY RUN] " if dry_run else ""
            self.stdout.write(
                self.style.SUCCESS(
                    f"{label}Skill videos created: {created}, updated: {updated}, skipped: {skipped}, errors: {errors}"
                )
            )

    def _clean_tier(self, value):
        tier = (value or "both").strip().lower()
        if tier not in {"foundation", "higher", "both"}:
            return "both"
        return tier

    def _clean_duration(self, value):
        try:
            duration = int(value)
        except (TypeError, ValueError):
            return 90
        return max(15, min(duration, 1200))

    def _clean_bool(self, value, default=False):
        if value is None or str(value).strip() == "":
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "y", "active"}
