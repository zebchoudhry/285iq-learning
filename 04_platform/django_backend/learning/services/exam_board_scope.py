"""
Resolve the student's exam board and filter questions valid for that board.
"""
from __future__ import annotations

from typing import Optional

from django.db.models import Q, QuerySet

from dashboard.models import ExamBoard
from learning.models import StudentExamSettings


SETTINGS_TO_CODE = {
    "aqa": "AQA",
    "edexcel": "EDEXCEL",
    "ocr": "OCR",
    "wjec": "WJEC",
}


def resolve_exam_board_id_for_student_subject(
    student_id: int,
    subject_id: int,
) -> Optional[int]:
    try:
        row = StudentExamSettings.objects.get(student_id=student_id, subject_id=subject_id)
    except StudentExamSettings.DoesNotExist:
        return None
    key = (row.exam_board or "").strip().lower()
    code = SETTINGS_TO_CODE.get(key)
    if not code:
        return None
    eb = ExamBoard.objects.filter(code__iexact=code, is_active=True).first()
    return eb.id if eb else None


def filter_questions_for_exam_board(
    qs: QuerySet,
    exam_board_id: Optional[int],
) -> QuerySet:
    if not exam_board_id:
        return qs
    return qs.filter(
        Q(is_shared=True)
        | Q(is_shared=False, specific_exam_boards__id=exam_board_id)
    ).distinct()
