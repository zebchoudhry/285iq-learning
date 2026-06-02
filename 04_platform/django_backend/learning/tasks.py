"""
Celery tasks for async LLM operations.

All heavy LLM calls are dispatched here so HTTP request handlers
return immediately and workers process in the background.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def task_build_weakness_digest(self, student_id: int, subject_id=None):
    """
    Async: build weakness digest for a student and cache result.
    Called after each practice session to keep the digest fresh.
    """
    try:
        from django.contrib.auth import get_user_model
        from learning.services.weakness_digest import build_weakness_digest
        from django.core.cache import cache

        User = get_user_model()
        student = User.objects.get(pk=student_id)
        result = build_weakness_digest(student, subject_id=subject_id)
        cache_key = f"weakness_digest:{student_id}:{subject_id or 'all'}"
        cache.set(cache_key, result, timeout=3600)
        logger.info("Weakness digest refreshed for student %s", student_id)
        return result
    except Exception as exc:
        logger.warning("task_build_weakness_digest failed for student %s: %s", student_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def task_llm_mark_calculation(self, attempt_id: int):
    """
    Async: run LLM partial marking on a calculation/extended attempt,
    then update the QuizAttempt.partial_marks field.
    """
    try:
        from learning.models import QuizAttempt
        from learning.services.answer_grading import llm_mark_calculation

        attempt = QuizAttempt.objects.select_related(
            "question__lesson__topic__subject"
        ).get(pk=attempt_id)
        question = attempt.question
        if question.question_type not in ("calculation", "extended"):
            return

        marks_avail = int(getattr(question, "marks_available", 1) or 1)
        raw_answer = attempt.student_answer or ""
        result = llm_mark_calculation(question, raw_answer, marks_avail)

        QuizAttempt.objects.filter(pk=attempt_id).update(
            partial_marks=result["marks_awarded"],
        )
        logger.info(
            "LLM marked attempt %s: %s/%s marks", attempt_id, result["marks_awarded"], marks_avail
        )
        return result
    except Exception as exc:
        logger.warning("task_llm_mark_calculation failed for attempt %s: %s", attempt_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=10)
def task_generate_worked_solution(self, question_id: int):
    """
    Async: generate and cache a worked solution for a question.
    """
    try:
        from learning.services.worked_solutions import get_worked_solution
        steps = get_worked_solution(question_id)
        logger.info("Worked solution generated for question %s (%d steps)", question_id, len(steps))
        return steps
    except Exception as exc:
        logger.warning("task_generate_worked_solution failed for question %s: %s", question_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=10)
def task_refresh_parent_dashboard(self, student_id: int):
    """
    Async: rebuild and cache the parent dashboard snapshot.
    """
    try:
        from django.contrib.auth import get_user_model
        from learning.services.dashboard_cache import invalidate_snapshot

        User = get_user_model()
        student = User.objects.get(pk=student_id)
        invalidate_snapshot(student_id)
        logger.info("Parent dashboard cache invalidated for student %s", student_id)
        return {"invalidated": True}
    except Exception as exc:
        logger.warning("task_refresh_parent_dashboard failed for student %s: %s", student_id, exc)
        raise self.retry(exc=exc)
