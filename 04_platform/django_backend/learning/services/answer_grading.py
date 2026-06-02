"""
Short-answer comparison with tolerant normalisation (STEM-friendly).
LLM-based partial marking for calculation/extended question types.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional, Tuple


def _normalise_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _strip_wrapping_punctuation(s: str) -> str:
    return s.strip(" \t\n\r.,;:!?\"'()[]{}|")


def _try_float(s: str) -> Optional[float]:
    t = s.replace(",", ".")
    t = re.sub(r"[^\d.\-+eE]", "", t)
    if not t or t in (".", "-", "+"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _numeric_close(a: str, b: str, rel_tol: float = 1e-4, abs_tol: float = 1e-6) -> bool:
    fa, fb = _try_float(a), _try_float(b)
    if fa is None or fb is None:
        return False
    if fa == fb:
        return True
    diff = abs(fa - fb)
    if diff <= abs_tol:
        return True
    scale = max(abs(fa), abs(fb), 1e-12)
    return diff / scale <= rel_tol


def _split_answer_tokens(s: str) -> list[str]:
    parts = re.split(r"\s+or\s+|;\s*|,\s*", s, flags=re.IGNORECASE)
    return [_strip_wrapping_punctuation(p) for p in parts if _strip_wrapping_punctuation(p)]


def answers_equivalent(student_answer: str, correct_answer: str) -> Tuple[bool, str]:
    """
    Return (is_equivalent, method) where method is 'exact', 'numeric', 'token_set', or 'none'.
    """
    sa = _normalise_text(student_answer or "")
    ca = _normalise_text(correct_answer or "")
    if not sa or not ca:
        return False, "none"

    sa_cmp = re.sub(r"\s*([=+\-*/])\s*", r"\1", sa.replace(" ", ""))
    ca_cmp = re.sub(r"\s*([=+\-*/])\s*", r"\1", ca.replace(" ", ""))
    if sa_cmp == ca_cmp:
        return True, "exact"

    if sa == ca:
        return True, "exact"

    if _numeric_close(sa, ca):
        return True, "numeric"

    stoks = sorted(_split_answer_tokens(sa))
    ctoks = sorted(_split_answer_tokens(ca))
    if stoks and ctoks and len(stoks) == len(ctoks):
        if all(
            a == b or _numeric_close(a, b)
            for a, b in zip(stoks, ctoks)
        ):
            return True, "token_set"

    if stoks and ctoks and all(_try_float(t) is not None for t in stoks + ctoks):
        if sorted(float(_try_float(t)) for t in stoks) == sorted(float(_try_float(t)) for t in ctoks):
            return True, "token_set"

    return False, "none"


import json
import re as _re


def llm_mark_calculation(question, student_working: str, marks_available: int) -> dict:
    """
    Use LLM to award partial marks for a calculation/extended answer.

    Returns:
        {"marks_awarded": int, "is_correct": bool, "feedback": str, "llm_used": bool}
    """
    from django.conf import settings

    backend = (getattr(settings, "LLM_BACKEND", "disabled") or "disabled").lower()
    if backend in ("disabled", "none"):
        return _fallback_partial(student_working, question.correct_answer, marks_available)

    topic = getattr(getattr(getattr(question, "lesson", None), "topic", None), "name", "STEM")
    subject = getattr(getattr(getattr(getattr(question, "lesson", None), "topic", None), "subject", None), "display_name", "Science")

    prompt = f"""You are a GCSE {subject} examiner marking a student's answer.

Question ({marks_available} marks): {question.question_text[:600]}

Mark scheme / correct answer: {question.correct_answer[:400]}

Student's working and answer:
{(student_working or "").strip()[:800]}

Award marks 0 to {marks_available}. Be fair: award method marks for correct working even if the final answer is wrong.
Return ONLY valid JSON: {{"marks_awarded": <int 0-{marks_available}>, "feedback": "<one sentence>", "is_correct": <true/false>}}
Example: {{"marks_awarded": 2, "feedback": "Correct method but arithmetic error in final step.", "is_correct": false}}"""

    try:
        from learning.services.llm_service import generate as llm_generate
        raw = llm_generate(prompt=prompt, max_tokens=150, temperature=0.1)
        raw = raw.strip()
        raw = _re.sub(r"^```(?:json)?\s*", "", raw)
        raw = _re.sub(r"\s*```$", "", raw)
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            data = json.loads(raw[start:end + 1])
            marks = max(0, min(int(data.get("marks_awarded", 0)), marks_available))
            return {
                "marks_awarded": marks,
                "is_correct": bool(data.get("is_correct", marks == marks_available)),
                "feedback": str(data.get("feedback", ""))[:300],
                "llm_used": True,
            }
    except Exception:
        pass

    return _fallback_partial(student_working, question.correct_answer, marks_available)


def _fallback_partial(student_working: str, correct_answer: str, marks_available: int) -> dict:
    """Token-overlap fallback when LLM unavailable."""
    answer = (student_working or "").strip().lower()
    correct = (correct_answer or "").strip().lower()
    if not answer or not correct:
        return {"marks_awarded": 0, "is_correct": False, "feedback": "", "llm_used": False}
    is_eq, _ = answers_equivalent(answer, correct)
    if is_eq:
        return {"marks_awarded": marks_available, "is_correct": True, "feedback": "", "llm_used": False}
    atoks = set(answer.replace(",", " ").split())
    ctoks = set(correct.replace(",", " ").split())
    ratio = len(atoks & ctoks) / max(1, len(ctoks))
    marks = 0
    if ratio >= 0.6:
        marks = min(marks_available - 1, max(1, int(round(marks_available * 0.5))))
    elif ratio >= 0.35 and marks_available > 1:
        marks = 1
    return {"marks_awarded": marks, "is_correct": False, "feedback": "", "llm_used": False}
