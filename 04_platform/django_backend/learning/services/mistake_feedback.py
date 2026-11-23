"""
Automatic feedback for wrong answers.

For every wrong answer this decides what kind of mistake it was
(conceptual / procedural / structural / guess) and writes:
  - a hint that helps the student retry without giving the answer away
  - a full explanation for when they have run out of retries

The mistake type is saved on QuizAttempt.error_type, which the gym-mode
engine uses to choose between drill, guided practice and instruction.

Uses the configured LLM when one is enabled; otherwise falls back to
simple rules plus the question's stored explanation, so it never blocks
an answer submission.
"""
import json
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

AI_ERROR_TYPES = ("conceptual", "procedural", "structural", "guess")

# Answers faster than this are treated as guesses (only when timing is sent).
GUESS_TIME_MS = 4000
# Numeric answers within this relative distance of the correct value are
# treated as a slip in method or arithmetic, not a misunderstanding.
NEAR_MISS_RATIO = 0.1

ERROR_LABELS = {
    "conceptual": "Concept gap",
    "procedural": "Method slip",
    "structural": "Logic error",
    "guess": "Looks like a guess",
}

RULE_HINTS = {
    "conceptual": "Go back over the key idea behind this question, then try again.",
    "procedural": "You're close. Check your working step by step: arithmetic, units and rounding.",
    "structural": "Check the order of your steps and that each one follows from the last.",
    "guess": "Take your time and work it through before answering.",
}

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _first_number(text):
    m = _NUMBER_RE.search((text or "").replace(",", ""))
    return float(m.group()) if m else None


def classify_by_rules(student_answer, correct_answer, time_spent_ms=None, is_multiple_choice=False):
    """Cheap, deterministic mistake classification."""
    answer = (student_answer or "").strip()
    if not answer:
        return "guess"
    if time_spent_ms and 0 < time_spent_ms < GUESS_TIME_MS:
        return "guess"
    if not is_multiple_choice:
        given, expected = _first_number(answer), _first_number(correct_answer)
        if given is not None and expected is not None:
            if expected == 0:
                near = abs(given) <= NEAR_MISS_RATIO
            else:
                near = abs(given - expected) / abs(expected) <= NEAR_MISS_RATIO
            # Same digits in a different place (e.g. 2.5 vs 25) is also a slip.
            same_digits = given != 0 and str(abs(given)).replace(".", "").strip("0") == str(abs(expected)).replace(".", "").strip("0")
            if near or same_digits:
                return "procedural"
    return "conceptual"


def _build_prompt(question, student_answer, correct_answer):
    subject = "GCSE"
    try:
        subject = question.lesson.topic.subject.display_name or subject
    except AttributeError:
        pass
    return "\n".join([
        f"A {subject} student answered this question incorrectly.",
        "",
        f"Question: {question.question_text}",
        f"Student's answer: {student_answer or '(blank)'}",
        f"Correct answer: {correct_answer}",
        "",
        "Classify the mistake as exactly one of:",
        "- conceptual: misunderstands the underlying idea",
        "- procedural: right idea, slip in method, arithmetic, units or rounding",
        "- structural: steps in the wrong order or reasoning that doesn't follow",
        "- guess: answer bears no relation to any reasonable attempt",
        "",
        "Reply with only a JSON object, no other text:",
        '{"error_type": "...", "hint": "...", "explanation": "..."}',
        "hint: one or two sentences pointing at what went wrong WITHOUT revealing the correct answer.",
        "explanation: up to four short sentences explaining the mistake and how to get the correct answer.",
        "Write for a 15-year-old in plain English using correct GCSE terms. No markdown.",
    ])


def _parse_ai_reply(text):
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
    except ValueError:
        return None
    error_type = str(data.get("error_type", "")).strip().lower()
    hint = str(data.get("hint", "")).strip()
    explanation = str(data.get("explanation", "")).strip()
    if error_type not in AI_ERROR_TYPES or not explanation:
        return None
    return {"error_type": error_type, "hint": hint, "explanation": explanation}


def _ai_enabled():
    backend = (getattr(settings, "LLM_BACKEND", "disabled") or "disabled").lower()
    return backend not in ("disabled", "none", "mock") and bool(getattr(settings, "LLM_USE_TUTOR", True))


def diagnose_wrong_answer(question, student_answer, time_spent_ms=None, is_multiple_choice=False):
    """
    Return {"error_type", "label", "hint", "explanation", "source"} for a wrong answer.
    Never raises.
    """
    correct_answer = question.correct_answer or ""
    if is_multiple_choice and not correct_answer:
        correct = question.options.filter(is_correct=True).first()
        correct_answer = getattr(correct, "option_text", "") or ""

    rule_type = classify_by_rules(student_answer, correct_answer, time_spent_ms, is_multiple_choice)
    result = {
        "error_type": rule_type,
        "hint": RULE_HINTS[rule_type],
        "explanation": question.explanation or "",
        "source": "rules",
    }

    # Blank or too-fast answers are guesses whatever the model says, and
    # aren't worth paying for an explanation of the student's reasoning.
    if rule_type != "guess" and _ai_enabled():
        try:
            from learning.services.llm_service import generate
            parsed = _parse_ai_reply(
                generate(_build_prompt(question, student_answer, correct_answer), max_tokens=600)
            )
            if parsed:
                result.update(parsed, source="ai")
                if not result["hint"]:
                    result["hint"] = RULE_HINTS[result["error_type"]]
        except Exception:
            logger.warning("AI mistake feedback failed for question %s", question.id, exc_info=True)

    result["label"] = ERROR_LABELS[result["error_type"]]
    return result
