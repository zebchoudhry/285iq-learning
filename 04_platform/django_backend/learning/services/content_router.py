from typing import Dict, Optional

from learning.models import Lesson, Question
from learning.services.exam_board_scope import filter_questions_for_exam_board


def _question_base_q(topic_id: int, exam_board_id: Optional[int] = None):
    qs = Question.objects.filter(
        lesson__topic_id=topic_id,
        is_active=True,
    )
    return filter_questions_for_exam_board(qs, exam_board_id)


def select_content_for_mode(
    *,
    mode: str,
    student_id: int,
    topic_id: int,
    limit: int = 10,
    use_llm: bool = False,
    exam_board_id: Optional[int] = None,
) -> Dict:
    """
    Return content IDs appropriate for the given gym mode.
    This function is deterministic and side-effect free.
    """

    if mode == "instruction":
        lessons = (
            Lesson.objects.filter(
                topic_id=topic_id,
                is_active=True,
            )
            .order_by("order")
            .values("id", "title", "lesson_type")[:limit]
        )

        return {
            "content_type": "lessons",
            "items": list(lessons),
        }

    if mode == "guided_practice":
        if use_llm:
            from learning.services.llm_question_generator import generate_questions

            ids = generate_questions(topic_id=topic_id, mode=mode, difficulty=2, count=6)
            if ids:
                qqs = _question_base_q(topic_id, exam_board_id).filter(id__in=ids)
                items = list(
                    qqs.order_by("difficulty_level", "id").values(
                        "id", "question_type", "marks_available"
                    )
                )
                return {"content_type": "questions", "items": items}

        questions = (
            _question_base_q(topic_id, exam_board_id)
            .filter(difficulty_level__lte=2)
            .order_by("difficulty_level", "id")
            .values("id", "question_type", "marks_available")[:limit]
        )

        return {
            "content_type": "questions",
            "items": list(questions),
        }

    if mode == "drill":
        if use_llm:
            from learning.services.llm_question_generator import generate_questions

            ids = generate_questions(topic_id=topic_id, mode=mode, difficulty=3, count=6)
            if ids:
                qqs = _question_base_q(topic_id, exam_board_id).filter(id__in=ids)
                items = list(
                    qqs.order_by("difficulty_level", "id").values(
                        "id", "question_type", "difficulty_level"
                    )
                )
                return {"content_type": "questions", "items": items}

        questions = (
            _question_base_q(topic_id, exam_board_id)
            .order_by("difficulty_level")
            .values("id", "question_type", "difficulty_level")[:limit]
        )

        return {
            "content_type": "questions",
            "items": list(questions),
        }

    if mode == "mixed_practice":
        if use_llm:
            from learning.services.llm_question_generator import generate_questions

            ids = generate_questions(topic_id=topic_id, mode=mode, difficulty=3, count=6)
            if ids:
                qqs = _question_base_q(topic_id, exam_board_id).filter(id__in=ids)
                items = list(
                    qqs.order_by("?").values("id", "question_type", "difficulty_level")
                )
                return {"content_type": "questions", "items": items}

        questions = (
            _question_base_q(topic_id, exam_board_id)
            .order_by("?")
            .values("id", "question_type", "difficulty_level")[:limit]
        )

        return {
            "content_type": "questions",
            "items": list(questions),
        }

    if mode == "exam_sim":
        if use_llm:
            from learning.services.llm_question_generator import generate_questions

            ids = generate_questions(topic_id=topic_id, mode=mode, difficulty=4, count=6)
            if ids:
                qqs = _question_base_q(topic_id, exam_board_id).filter(id__in=ids)
                items = list(
                    qqs.order_by("difficulty_level", "-marks_available").values(
                        "id", "marks_available"
                    )
                )
                return {
                    "content_type": "exam_questions",
                    "items": items,
                    "timer_required": True,
                }

        questions = (
            _question_base_q(topic_id, exam_board_id)
            .filter(difficulty_level__gte=3)
            .order_by("difficulty_level", "-marks_available")
            .values("id", "marks_available")[:limit]
        )

        return {
            "content_type": "exam_questions",
            "items": list(questions),
            "timer_required": True,
        }

    if mode == "mastery_maintenance":
        questions = (
            _question_base_q(topic_id, exam_board_id)
            .order_by("?")
            .values("id")[:5]
        )

        return {
            "content_type": "light_review",
            "items": list(questions),
        }

    return {
        "content_type": "none",
        "items": [],
    }
