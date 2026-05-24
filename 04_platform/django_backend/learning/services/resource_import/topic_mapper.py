"""
Topic mapper - maps external resource sections/folders to platform Subject, Topic, Lesson.
Uses _meta/TOPIC_MAPPING.json from 285data.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Default path to 285data _meta folder (sibling of 285iq_learning)
_PROJECT_ROOT = Path(__file__).resolve().parents[5]  # 285iq_learning
DEFAULT_META_PATH = _PROJECT_ROOT.parent / "285data" / "_meta"


def load_topic_mapping(meta_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load TOPIC_MAPPING.json from 285data/_meta."""
    path = meta_path or DEFAULT_META_PATH
    mapping_file = Path(path) / "TOPIC_MAPPING.json"
    if not mapping_file.exists():
        return {}
    with open(mapping_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_topic_mapping(
    subject_key: str,
    folder_name: str,
    meta_path: Optional[Path] = None,
) -> Optional[Dict[str, str]]:
    """
    Get Subject and Topic names for a given subject and folder.
    Returns {"subject_name": "Biology", "topic_name": "Cell Biology"} or None.
    """
    mapping = load_topic_mapping(meta_path)
    if not mapping:
        return None

    subject_data = mapping.get(subject_key)
    if not subject_data:
        return None

    topics = subject_data.get("topics", {})
    topic_name = topics.get(folder_name) or topics.get(folder_name.replace(" ", "-"))
    if not topic_name:
        return None

    return {
        "subject_name": subject_data.get("subject_name", subject_key.title()),
        "topic_name": topic_name,
    }


def map_note_section_to_lesson(
    section_id: str,
    section_title: str,
    subject_key: str,
    topic_folder: str,
    meta_path: Optional[Path] = None,
) -> Optional[str]:
    """
    Map a note section (e.g. "1.1.1", "Eukaryotes and Prokaryotes") to a lesson title.
    Returns lesson title string or None if no mapping.
    """
    mapping = load_topic_mapping(meta_path)
    if not mapping:
        return None

    subject_data = mapping.get(subject_key)
    if not subject_data:
        return None

    section_map = subject_data.get("note_sections_to_lessons", {})
    # Try section_id first (e.g. "1.1.1")
    lesson = section_map.get(section_id)
    if lesson:
        return lesson
    # Try section_title (e.g. "Eukaryotes and Prokaryotes")
    lesson = section_map.get(section_title)
    if lesson:
        return lesson
    # Try truncated section_id (e.g. "1.1" -> "1.1.1" might map "1.1")
    if "." in section_id:
        parent = section_id.rsplit(".", 1)[0]
        return section_map.get(parent)
    return None


def get_all_folder_mappings(subject_key: str, meta_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Get all folder -> topic_name mappings for a subject.
    Returns {"cell-biology": "Cell Biology", "organisation": "Organisation", ...}
    """
    mapping = load_topic_mapping(meta_path)
    if not mapping:
        return {}

    subject_data = mapping.get(subject_key)
    if not subject_data:
        return {}

    return subject_data.get("topics", {})
