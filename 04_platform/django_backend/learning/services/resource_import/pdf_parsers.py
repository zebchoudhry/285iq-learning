"""
PDF parsers for GCSE resource import.
Handles MEGA Lecture / PMT worksheet format, detailed notes, and definitions.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF using pdfplumber."""
    if not HAS_PDFPLUMBER:
        raise ImportError("pdfplumber required: pip install pdfplumber")
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n\n".join(text_parts)


def parse_worksheet_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parse MEGA Lecture / PMT worksheet format: Q1. ... Answer: ... (or Solution: ...)
    Returns list of {question_text, correct_answer, question_number, source}.
    """
    text = _extract_text_from_pdf(pdf_path)
    questions = []

    # Pattern: Q{N}. {question} Answer: {answer} (or Solution:)
    # Answer/Solution can span multiple lines until next Q or end
    pattern = re.compile(
        r'Q(\d+)\.\s*(.+?)(?=Answer:|Solution:)(?:Answer:|Solution:)\s*(.+?)(?=Q\d+\.|www\.|$)',
        re.DOTALL | re.IGNORECASE
    )

    # Split by Q1. Q2. (MEGA/PMT) or line-start 1. 2. (Corbett style)
    blocks = re.split(r'(?=Q\d+\.)|(?=^(?:\d+)\.\s)', text, flags=re.MULTILINE)
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 15:
            continue

        # Try Q1. format first
        q_match = re.match(r'Q?(\d+)\.\s*(.+?)(?=Answer:|Solution:|Q?\d+\.|$)', block, re.DOTALL | re.IGNORECASE)
        if not q_match:
            continue

        q_num = q_match.group(1)
        q_text = q_match.group(2).strip()

        # Answer may be in same block (Answer:) or separate file
        ans_match = re.search(r'(?:Answer:|Solution:)\s*(.+?)(?=Q?\d+\.|www\.|$)', block, re.DOTALL | re.IGNORECASE)
        answer = ans_match.group(1).strip() if ans_match else ""

        # Clean up: remove page markers, URLs
        q_text = re.sub(r'www\.[^\s]+', '', q_text).strip()
        q_text = re.sub(r'--\s*\d+\s+of\s+\d+\s*--', '', q_text).strip()
        answer = re.sub(r'www\.[^\s]+', '', answer).strip()
        answer = re.sub(r'--\s*\d+\s+of\s+\d+\s*--', '', answer).strip()

        if len(q_text) >= 10:
            questions.append({
                "question_number": int(q_num),
                "question_text": q_text,
                "correct_answer": answer,
                "source": Path(pdf_path).name,
            })

    return questions


def parse_notes_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parse detailed notes PDF into sections. PMT/MEGA format with headers like:
    "Cell Structure (1.1)", "Eukaryotes and Prokaryotes (1.1.1)", "Animals and Plants (1.1.2)"
    Returns list of {section_id, section_title, content}.
    """
    text = _extract_text_from_pdf(pdf_path)
    sections = _split_notes_by_headers(text)
    if not sections and text.strip():
        return [{"section_id": "1", "section_title": "Notes", "content": text.strip()}]
    return sections


def _split_notes_by_headers(text: str) -> List[Dict[str, Any]]:
    """Alternative: split by lines that look like headers (e.g. 'Cell Structure (1.1)')."""
    sections = []
    lines = text.split('\n')
    current_title = None
    current_id = None
    current_content = []

    for line in lines:
        match = re.match(r'^(.+?)\s*\((\d+(?:\.\d+)*)\)\s*$', line.strip())
        if match:
            if current_title is not None:
                sections.append({
                    "section_id": current_id or "",
                    "section_title": current_title,
                    "content": "\n".join(current_content).strip(),
                })
            current_title = match.group(1).strip()
            current_id = match.group(2)
            current_content = []
        else:
            current_content.append(line)

    if current_title is not None:
        sections.append({
            "section_id": current_id or "",
            "section_title": current_title,
            "content": "\n".join(current_content).strip(),
        })

    return sections


def parse_definitions_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parse definitions PDF. Format varies; common: "Term: definition" or "Term - definition".
    Returns list of {term, definition}. Note: scanned PDFs may need OCR - this handles text-based.
    """
    text = _extract_text_from_pdf(pdf_path)

    # If text is mostly garbled (encoding issue), return empty
    if len(text) > 0 and text.count('\x00') > len(text) // 2:
        return []

    definitions = []

    # Pattern 1: Term: definition
    for match in re.finditer(r'^([^:\n]+):\s*(.+?)(?=^[^:\n]+:|\Z)', text, re.MULTILINE | re.DOTALL):
        term = match.group(1).strip()
        definition = match.group(2).strip()
        if term and definition and len(term) < 80 and len(definition) > 5:
            definitions.append({"term": term, "definition": definition})

    # Pattern 2: Term - definition (if pattern 1 found little)
    if len(definitions) < 3:
        for match in re.finditer(r'^([^-\n]+)\s*-\s*(.+?)(?=^[^\n]+\s*-\s*|\Z)', text, re.MULTILINE | re.DOTALL):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if term and definition and len(term) < 80 and len(definition) > 5:
                definitions.append({"term": term, "definition": definition})

    return definitions
