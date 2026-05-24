"""
Seed/update all lesson titles across GCSE subjects from a titles file.

File format: titles grouped by subject and topic, numbered like "1.1 Title", "2.3 Title".
Lines starting with # are subject headers (e.g. "# Mathematics").

Usage:
  python manage.py seed_all_titles
  python manage.py seed_all_titles --dry-run
  python manage.py seed_all_titles --subject mathematics
  python manage.py seed_all_titles --file "path/to/gcse_lesson_titles.txt"
"""
import os
import re
from pathlib import Path

from django.core.management.base import BaseCommand

from learning.models import Subject, Topic, Lesson


# Default file path: maths subs folder on Desktop, then project data folder
DEFAULT_PATHS = [
    Path.home() / "Desktop" / "maths subs" / "gcse_lesson_titles.txt",
    Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "gcse_lesson_titles.txt",
]

# Map subject names in file to DB name patterns (case-insensitive)
SUBJECT_ALIASES = {
    "mathematics": ["mathematics", "math", "maths"],
    "biology": ["biology"],
    "chemistry": ["chemistry", "chem"],
    "physics": ["physics", "phys"],
}


class Command(BaseCommand):
    help = "Update all lesson titles from a GCSE lesson titles file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without saving",
        )
        parser.add_argument(
            "--subject",
            type=str,
            help="Run for one subject only (e.g. mathematics, biology)",
        )
        parser.add_argument(
            "--file",
            type=str,
            help="Path to titles file (default: maths subs/gcse_lesson_titles.txt)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        subject_filter = options.get("subject")
        file_path = options.get("file")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be saved"))
            self.stdout.write("")

        # Resolve file path
        if file_path:
            path = Path(file_path)
        else:
            path = None
            for p in DEFAULT_PATHS:
                if p.exists():
                    path = p
                    break
            if not path:
                self.stdout.write(
                    self.style.ERROR(
                        "Titles file not found. Use --file to specify path, or place "
                        "gcse_lesson_titles.txt in 'maths subs' on Desktop."
                    )
                )
                return

        if not path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {path}"))
            return

        self.stdout.write(f"Reading: {path}")
        self.stdout.write("")

        # Parse file
        parsed = self._parse_file(path)
        if not parsed:
            self.stdout.write(self.style.ERROR("No valid content parsed from file."))
            return

        # Filter by subject if requested
        if subject_filter:
            subject_filter_lower = subject_filter.lower()
            parsed = {
                k: v
                for k, v in parsed.items()
                if k.lower() == subject_filter_lower or subject_filter_lower in k.lower()
            }
            if not parsed:
                self.stdout.write(
                    self.style.ERROR(f"No subject matching '{subject_filter}' in file.")
                )
                return

        # Process each subject
        totals = {"updated": 0, "created": 0, "skipped": 0}
        per_subject = {}

        for subject_name, lessons_by_topic in parsed.items():
            result = self._process_subject(
                subject_name, lessons_by_topic, dry_run=dry_run
            )
            per_subject[subject_name] = result
            totals["updated"] += result["updated"]
            totals["created"] += result["created"]
            totals["skipped"] += result["skipped"]

        # Summary
        self._print_summary(per_subject, totals, dry_run)

    def _parse_file(self, path):
        """
        Parse titles file. Returns dict:
        { "Mathematics": { 1: [(1, "Title1"), (2, "Title2")], 2: [(1, "Title")] }, ... }
        """
        result = {}
        current_subject = None
        # Regex: "1.1 Title" or "2.10 Some Title"
        pattern = re.compile(r"^(\d+)\.(\d+)\s+(.+)$")

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                if line.startswith("#"):
                    # Subject header: # Mathematics
                    current_subject = line.lstrip("#").strip()
                    if current_subject:
                        result[current_subject] = {}
                    continue
                m = pattern.match(line)
                if m and current_subject:
                    topic_num = int(m.group(1))
                    lesson_num = int(m.group(2))
                    title = m.group(3).strip()
                    if topic_num not in result[current_subject]:
                        result[current_subject][topic_num] = []
                    result[current_subject][topic_num].append((lesson_num, title))

        return result

    def _find_subject(self, subject_name):
        """Find Subject by name (case-insensitive)."""
        name_lower = subject_name.lower()
        # Try exact match first
        subject = Subject.objects.filter(name__iexact=name_lower).first()
        if subject:
            return subject
        # Try aliases
        for db_name, aliases in SUBJECT_ALIASES.items():
            if name_lower in aliases or name_lower == db_name:
                subject = Subject.objects.filter(name__iexact=db_name).first()
                if subject:
                    return subject
        return None

    def _process_subject(self, subject_name, lessons_by_topic, dry_run=False):
        """Process one subject. Returns {updated, created, skipped}."""
        subject = self._find_subject(subject_name)
        if not subject:
            self.stdout.write(
                self.style.WARNING(
                    f"  Subject '{subject_name}' not found in database (skipping)"
                )
            )
            return {"updated": 0, "created": 0, "skipped": 0}

        self.stdout.write(f"Subject: {subject.display_name} ({subject.name})")

        updated = 0
        created = 0
        skipped = 0

        # Get topics ordered by order field
        topics_list = list(
            Topic.objects.filter(subject=subject, is_active=True).order_by("order")
        )

        for topic_num, lesson_list in sorted(lessons_by_topic.items()):
            # Match topic by order number (1-based position)
            if topic_num < 1 or topic_num > len(topics_list):
                self.stdout.write(
                    self.style.WARNING(
                        f"  Topic {topic_num} not found (subject has {len(topics_list)} topics)"
                    )
                )
                skipped += len(lesson_list)
                continue

            topic = topics_list[topic_num - 1]
            self.stdout.write(f"  Topic {topic_num}: {topic.name}")

            for lesson_num, title in lesson_list:
                full_title = f"{topic_num}.{lesson_num} - {title}"
                # Lesson order is 0-based
                lesson_order = lesson_num - 1

                try:
                    lesson = Lesson.objects.get(
                        topic=topic, order=lesson_order, is_active=True
                    )
                    if lesson.title != full_title:
                        if dry_run:
                            self.stdout.write(
                                f"    [UPDATE] {lesson.title!r} -> {full_title!r}"
                            )
                        else:
                            lesson.title = full_title
                            lesson.save(update_fields=["title"])
                        updated += 1
                    else:
                        skipped += 1
                except Lesson.DoesNotExist:
                    default_content = f"Learning materials for {title}"
                    if dry_run:
                        self.stdout.write(
                            f"    [CREATE] {full_title!r} (content: {default_content!r})"
                        )
                    else:
                        Lesson.objects.create(
                            topic=topic,
                            title=full_title,
                            content=default_content,
                            order=lesson_order,
                            lesson_type="theory",
                            difficulty_level=2,
                            estimated_duration=30,
                            is_active=True,
                        )
                    created += 1

        self.stdout.write(
            f"  -> Updated: {updated}, Created: {created}, Skipped: {skipped}"
        )
        return {"updated": updated, "created": created, "skipped": skipped}

    def _print_summary(self, per_subject, totals, dry_run):
        """Print full summary per subject and totals."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS("SUMMARY" + (" (DRY RUN)" if dry_run else ""))
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        for subject_name, stats in per_subject.items():
            self.stdout.write(f"  {subject_name}:")
            self.stdout.write(f"    Updated: {stats['updated']}")
            self.stdout.write(f"    Created: {stats['created']}")
            self.stdout.write(f"    Skipped: {stats['skipped']}")
            self.stdout.write("")

        self.stdout.write("  TOTAL:")
        self.stdout.write(f"    Updated: {totals['updated']}")
        self.stdout.write(f"    Created: {totals['created']}")
        self.stdout.write(f"    Skipped: {totals['skipped']}")
        self.stdout.write("")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Run without --dry-run to apply changes."
                )
            )
        self.stdout.write(self.style.SUCCESS("=" * 60))
