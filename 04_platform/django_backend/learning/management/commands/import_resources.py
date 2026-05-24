"""
Import GCSE resources from 285data folder into the platform.
Parses worksheets, notes, definitions and creates Question/Lesson records.
"""
import re
import sys
from pathlib import Path

from django.core.management.base import BaseCommand


def _safe_write(text: str) -> str:
    """Encode text for Windows console (replace non-ASCII if needed)."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        return text.encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding)
    return text

from learning.models import Subject, Topic, Lesson, Question
from learning.services.resource_import import (
    parse_worksheet_pdf,
    parse_notes_pdf,
    parse_definitions_pdf,
    get_topic_mapping,
    map_note_section_to_lesson,
    load_topic_mapping,
)

# File patterns for auto-detection (case-insensitive)
WORKSHEET_PATTERNS = [
    r"worksheets?\.pdf",
    r"worksheet.*\.pdf",
    r".*worksheets?.*\.pdf",
]
NOTES_PATTERNS = [
    r"notes?\.pdf",
    r"detailed-?notes?.*\.pdf",
    r".*notes?.*\.pdf",
]
DEFINITIONS_PATTERNS = [
    r"definitions?\.pdf",
    r".*definitions?.*\.pdf",
]
QUESTIONS_PATTERNS = [
    r"questions?\.pdf",
    r".*questions?.*\.pdf",
]
ANSWERSHEET_PATTERNS = [
    r"answers?heet?\.pdf",
    r".*answers?.*\.pdf",
]


def _match_file(patterns: list, name: str) -> bool:
    return any(re.search(p, name, re.I) for p in patterns)


class Command(BaseCommand):
    help = "Import GCSE resources from 285data folder into the platform"

    def add_arguments(self, parser):
        parser.add_argument(
            "--subject",
            type=str,
            default="biology",
            help="Subject key: biology, chemistry, physics, mathematics, or 'all'",
        )
        parser.add_argument(
            "--topic",
            type=str,
            help="Topic name or folder (e.g. 'Cell Biology' or 'cell-biology')",
        )
        parser.add_argument(
            "--path",
            type=str,
            help="Path to topic folder containing PDFs (e.g. 285data/biology/cell-biology)",
        )
        parser.add_argument(
            "--meta-path",
            type=str,
            default=None,
            help="Path to 285data/_meta (default: sibling of project)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and show what would be imported, without writing to DB",
        )

    def handle(self, *args, **options):
        subject_key = options["subject"].lower()
        topic_arg = options["topic"]
        path_arg = options["path"]
        meta_path = Path(options["meta_path"]) if options["meta_path"] else None
        dry_run = options["dry_run"]

        if subject_key == "all":
            self._batch_import(meta_path, dry_run)
            return

        if not path_arg:
            self.stdout.write(self.style.ERROR("--path is required (or use --subject all)"))
            return

        path = Path(path_arg)
        if not path.is_dir():
            self.stdout.write(self.style.ERROR(f"Path not found: {path}"))
            return

        folder_name = path.name.replace(" ", "-").lower() or path.name
        topic_mapping = get_topic_mapping(subject_key, folder_name, meta_path)
        if not topic_mapping:
            topic_mapping = get_topic_mapping(subject_key, path.name, meta_path)
        if not topic_mapping:
            self.stdout.write(
                self.style.WARNING(
                    f"No topic mapping for subject={subject_key} folder={path.name}. "
                    "Check _meta/TOPIC_MAPPING.json"
                )
            )
            return

        subject_name = topic_mapping["subject_name"]
        topic_name = topic_mapping["topic_name"]

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would import: {subject_name} / {topic_name} from {path}"
                )
            )

        self._import_folder(
            path=path,
            subject_key=subject_key,
            subject_name=subject_name,
            topic_name=topic_name,
            dry_run=dry_run,
        )

    def _batch_import(self, meta_path, dry_run):
        mapping = load_topic_mapping(meta_path)
        if not mapping:
            self.stdout.write(
                self.style.ERROR("Could not load TOPIC_MAPPING.json. Is 285data/_meta present?")
            )
            return

        # Infer 285data path from meta_path
        meta = Path(meta_path) if meta_path else Path(__file__).resolve().parents[5].parent / "285data" / "_meta"
        data_root = meta.parent

        subject_folders = {
            "biology": ["Biol", "biology", "Biology"],
            "chemistry": ["chemistry", "Chemistry", "chem"],
            "physics": ["physics", "Physics", "phys"],
            "mathematics": ["mathematics", "maths", "Maths", "math"],
        }

        for subj_key, folder_names in subject_folders.items():
            if subj_key not in mapping:
                continue
            for fn in folder_names:
                subj_path = data_root / fn
                if not subj_path.is_dir():
                    continue
                for topic_dir in subj_path.iterdir():
                    if not topic_dir.is_dir():
                        continue
                    folder_name = topic_dir.name
                    topic_mapping = get_topic_mapping(subj_key, folder_name, meta_path)
                    if not topic_mapping:
                        topic_mapping = get_topic_mapping(
                            subj_key, folder_name.replace(" ", "-"), meta_path
                        )
                    if topic_mapping:
                        self.stdout.write(
                            self.style.SUCCESS(f"Importing: {subj_key} / {topic_mapping['topic_name']}")
                        )
                        self._import_folder(
                            path=topic_dir,
                            subject_key=subj_key,
                            subject_name=topic_mapping["subject_name"],
                            topic_name=topic_mapping["topic_name"],
                            dry_run=dry_run,
                        )
                break  # only first matching folder per subject

    def _import_folder(
        self,
        path: Path,
        subject_key: str,
        subject_name: str,
        topic_name: str,
        dry_run: bool,
    ):
        subject = Subject.objects.filter(name=subject_name).first()
        if not subject:
            self.stdout.write(
                self.style.WARNING(f"Subject '{subject_name}' not found. Run load_*_lessons first.")
            )
            return

        topic = Topic.objects.filter(subject=subject, name=topic_name).first()
        if not topic:
            self.stdout.write(
                self.style.WARNING(f"Topic '{topic_name}' not found. Run load_*_lessons first.")
            )
            return

        # Get first lesson for questions (or create a fallback)
        lessons = list(topic.lessons.filter(is_active=True).order_by("order"))
        default_lesson = lessons[0] if lessons else None

        # Scan for PDFs
        worksheets = []
        notes_files = []
        definitions_files = []

        for f in path.glob("*.pdf"):
            name = f.name
            if _match_file(WORKSHEET_PATTERNS, name) or "worksheet" in name.lower():
                worksheets.append(f)
            elif _match_file(QUESTIONS_PATTERNS, name):
                worksheets.append(f)  # Try parsing; may have Q+Answer or questions-only
            elif _match_file(ANSWERSHEET_PATTERNS, name):
                worksheets.append(f)  # Try parsing answer format
            elif _match_file(NOTES_PATTERNS, name) or "detailed" in name.lower():
                notes_files.append(f)
            elif _match_file(DEFINITIONS_PATTERNS, name):
                definitions_files.append(f)

        total_questions = 0

        # Import worksheets
        for pdf_path in worksheets:
            try:
                items = parse_worksheet_pdf(str(pdf_path))
                for item in items:
                    if dry_run:
                        self.stdout.write(
                            _safe_write(f"  [Q] {item['question_text'][:60]}...")
                        )
                    elif default_lesson:
                        q, created = Question.objects.get_or_create(
                            lesson=default_lesson,
                            question_text=item["question_text"][:5000],
                            defaults={
                                "correct_answer": item.get("correct_answer", "")[:5000],
                                "explanation": item.get("correct_answer", "")[:2000],
                                "source": item.get("source", pdf_path.name)[:100],
                                "question_type": "short_answer",
                            },
                        )
                        if created:
                            total_questions += 1
                if items:
                    self.stdout.write(
                        self.style.SUCCESS(f"  Worksheets: {len(items)} questions from {pdf_path.name}")
                    )
                    if dry_run:
                        total_questions += len(items)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error parsing {pdf_path.name}: {e}")
                )

        # Import notes -> update lesson content
        for pdf_path in notes_files:
            try:
                sections = parse_notes_pdf(str(pdf_path))
                for sec in sections:
                    lesson_title = map_note_section_to_lesson(
                        sec["section_id"],
                        sec["section_title"],
                        subject_key,
                        path.name,
                    )
                    if lesson_title and not dry_run:
                        lesson = next(
                            (l for l in lessons if lesson_title in l.title),
                            None,
                        )
                        if lesson:
                            try:
                                lesson.content = sec["content"][:10000]
                                lesson.save(update_fields=["content", "updated_at"])
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        _safe_write(f"  Notes: updated lesson '{lesson.title[:40]}...'")
                                    )
                                )
                            except Exception as save_err:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"  Skipped section {sec.get('section_id')}: {save_err}"
                                    )
                                )
                    elif dry_run and sec["section_id"] != "intro":
                        self.stdout.write(
                            _safe_write(
                                f"  [Note] {sec['section_id']} {sec['section_title']} -> {lesson_title or 'no mapping'}"
                            )
                        )
                if sections:
                    self.stdout.write(
                        self.style.SUCCESS(f"  Notes: {len(sections)} sections from {pdf_path.name}")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error parsing notes {pdf_path.name}: {e}")
                )

        # Import definitions as short-answer questions
        for pdf_path in definitions_files:
            try:
                items = parse_definitions_pdf(str(pdf_path))
                for item in items:
                    if dry_run:
                        self.stdout.write(
                            _safe_write(f"  [Def] {item['term']}: {item['definition'][:40]}...")
                        )
                    elif default_lesson:
                        q_text = f"What is {item['term']}?"
                        q, created = Question.objects.get_or_create(
                            lesson=default_lesson,
                            question_text=q_text[:5000],
                            defaults={
                                "correct_answer": item["definition"][:5000],
                                "source": f"Definitions - {pdf_path.name}"[:100],
                                "question_type": "short_answer",
                            },
                        )
                        if created:
                            total_questions += 1
                if items:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Definitions: {len(items)} terms from {pdf_path.name}"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error parsing definitions {pdf_path.name}: {e}")
                )

        if not dry_run and total_questions > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\nCompleted. Imported questions to {topic_name}.")
            )
