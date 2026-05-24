"""
Load questions from JSON files into the database.
Usage: python manage.py load_questions --file data/questions_mathematics.json [--subject mathematics] [--dry-run]
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from learning.models import Question
from learning.generators.base import resolve_lesson, create_question_from_dict


def _normalize_blocks(data):
    """Normalize JSON data into list of blocks. Each block has subject, topic, lesson, questions."""
    if isinstance(data, list):
        blocks = data
    elif isinstance(data, dict):
        if "questions" in data:
            blocks = [data]
        else:
            blocks = []
    else:
        return []
    out = []
    for b in blocks:
        if not isinstance(b, dict) or "questions" not in b:
            continue
        subj = b.get("subject") or b.get("Subject")
        topic = b.get("topic") or b.get("Topic")
        lesson = b.get("lesson") or b.get("Lesson")
        questions = b.get("questions")
        if questions and subj and topic and lesson:
            out.append({"subject": subj, "topic": topic, "lesson": lesson, "questions": questions})
    return out


class Command(BaseCommand):
    help = "Load questions from JSON file into the database"

    def add_arguments(self, parser):
        parser.add_argument("--file", "-f", type=str, required=True, help="Path to JSON file")
        parser.add_argument(
            "--subject",
            "-s",
            type=str,
            default=None,
            help="Optional: filter to subject name (case-insensitive)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be done without creating records",
        )

    def handle(self, *args, **options):
        filepath = Path(options["file"])
        subject_filter = (options["subject"] or "").strip() or None
        dry_run = options["dry_run"]
        if not filepath.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {filepath}"))
            return
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Invalid JSON: {e}"))
            return
        blocks = _normalize_blocks(data)
        if not blocks:
            self.stderr.write(self.style.WARNING("No valid question blocks found in JSON"))
            return
        created = 0
        skipped = 0
        errors = 0
        for block in blocks:
            subj_name = str(block["subject"]).strip()
            if subject_filter and subj_name.lower() != subject_filter.lower():
                continue
            subject, topic, lesson = resolve_lesson(
                block["subject"], block["topic"], block["lesson"]
            )
            if not lesson:
                self.stderr.write(
                    self.style.WARNING(
                        f"Could not resolve lesson: subject={block['subject']}, "
                        f"topic={block['topic']}, lesson={block['lesson']}"
                    )
                )
                errors += 1
                continue
            for q in block["questions"]:
                if not isinstance(q, dict):
                    errors += 1
                    continue
                qtext = (q.get("question_text") or "").strip()
                if not qtext:
                    continue
                if dry_run:
                    if Question.objects.filter(lesson=lesson, question_text=qtext).exists():
                        skipped += 1
                    else:
                        created += 1
                    continue
                q_obj, was_created = create_question_from_dict(lesson, q, skip_duplicates=True)
                if was_created:
                    created += 1
                else:
                    skipped += 1
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would create: {created}, skip (duplicate): {skipped}, errors: {errors}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created: {created}, skipped (duplicate): {skipped}, errors: {errors}"
                )
            )
