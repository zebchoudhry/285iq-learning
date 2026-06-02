"""
Worked solution generator — returns a step-by-step breakdown for any question.

Steps are cached on Question.worked_solution_cache (JSON) so the LLM is only
called once per question. Falls back to a minimal static solution if LLM is off.
"""
import json
import logging

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _build_prompt(question) -> str:
    subject = ''
    try:
        subject = question.lesson.topic.subject.display_name
    except Exception:
        subject = 'GCSE'

    marks = question.marks_available or 1
    scheme = question.marking_scheme or ''

    return (
        f"You are a GCSE {subject} examiner. Provide a worked solution for the following question.\n\n"
        f"Question: {question.question_text}\n"
        f"Correct answer: {question.correct_answer}\n"
        f"Marks available: {marks}\n"
        + (f"Marking scheme: {scheme}\n" if scheme else "")
        + "\nReturn a JSON array of step objects. Each step must have:\n"
        '  {"step": 1, "description": "What to do", "working": "Calculation or reasoning", "marks": 1}\n\n'
        "Rules:\n"
        "- One step per mark available\n"
        "- Use GCSE-level language\n"
        "- Show all working clearly\n"
        "- Return ONLY the JSON array, no other text"
    )


def _static_fallback(question) -> list:
    return [
        {
            "step": 1,
            "description": "Read the question carefully and identify what is being asked.",
            "working": "",
            "marks": 0,
        },
        {
            "step": 2,
            "description": "Apply the relevant formula or concept.",
            "working": f"Answer: {question.correct_answer}",
            "marks": question.marks_available or 1,
        },
    ]


def _parse_steps(text: str) -> list:
    text = text.strip()
    # strip markdown fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        data = json.loads(text[start:end + 1])
        return data if isinstance(data, list) else []
    except Exception:
        return []


def get_worked_solution(question_id: int) -> list:
    """
    Return a list of step dicts for the question.
    Served from cache when available; generated via LLM on first call.
    """
    from learning.models import Question

    try:
        question = Question.objects.select_related("lesson__topic__subject").get(id=question_id)
    except Question.DoesNotExist:
        return []

    # Return cached solution if present
    if question.worked_solution_cache:
        try:
            steps = json.loads(question.worked_solution_cache)
            if steps:
                logger.debug("Worked solution cache hit for question %s", question_id)
                return steps
        except Exception:
            pass

    use_llm = bool(getattr(settings, "LLM_USE_TUTOR", True))
    steps = []

    if use_llm:
        try:
            from learning.services.llm_service import generate as llm_generate
            raw = llm_generate(prompt=_build_prompt(question), max_tokens=800, temperature=0.2)
            steps = _parse_steps(raw)
        except Exception:
            logger.warning("LLM worked solution failed for question %s", question_id, exc_info=True)

    if not steps:
        steps = _static_fallback(question)

    # Persist to cache
    try:
        question.worked_solution_cache = json.dumps(steps)
        question.worked_solution_cached_at = timezone.now()
        question.save(update_fields=["worked_solution_cache", "worked_solution_cached_at"])
    except Exception:
        logger.warning("Failed to cache worked solution for question %s", question_id)

    return steps
