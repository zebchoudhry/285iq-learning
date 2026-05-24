"""
LLM step-level diagnostic: identify where the student gets stuck.
"""
import json
import re

from django.conf import settings

from learning.models import Question, QuestionStep


def _extract_diagnostic_json(text):
    """Parse LLM response for diagnostic JSON."""
    if not text:
        return None
    cleaned = text.strip()
    # Strip fenced code blocks
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None


def diagnose_stuck_step(
    question_id: int,
    student_answers: list,
    student_said_stuck: bool = False,
) -> dict:
    """
    Identify at which step the student got stuck or first went wrong.

    Args:
        question_id: Question ID
        student_answers: List of {"step_order": N, "student_answer": str}
                        or [{"step_order": 1, "student_answer": "..."}]
        student_said_stuck: True if student clicked "I'm stuck"

    Returns:
        {
            "stuck_at_step": int,
            "reason": str,
            "skill_code": str,
            "recommendation": str,
            "success": bool,
        }
    """
    try:
        question = Question.objects.select_related("lesson__topic__subject").get(
            id=question_id, is_active=True
        )
    except Question.DoesNotExist:
        return {"success": False, "reason": "Question not found"}

    steps = list(
        QuestionStep.objects.filter(question=question)
        .select_related("skill")
        .order_by("step_order")
    )

    subject_name = question.lesson.topic.subject.display_name
    topic_name = question.lesson.topic.name

    # Normalize student_answers
    answers_by_step = {}
    for a in student_answers or []:
        if isinstance(a, dict):
            so = a.get("step_order", a.get("step_order"))
            ans = a.get("student_answer", a.get("answer", ""))
            if so is not None:
                answers_by_step[int(so)] = str(ans or "").strip()

    if steps:
        # Multi-step: build prompt with steps and student answers
        step_lines = []
        for s in steps:
            step_lines.append(
                f"Step {s.step_order} (Skill: {s.skill.code}): {s.hint_level_1 or s.expected_expression or 'Solve this step'}"
            )
        steps_text = "\n".join(step_lines)

        answers_text = "\n".join(
            f"Step {so}: Student wrote '{ans}'"
            for so, ans in sorted(answers_by_step.items())
        ) or "No answers provided yet."

        prompt = f"""You are a GCSE tutor. A student is working through a multi-step {subject_name} question.

Question: {question.question_text[:800]}

Steps (in order):
{steps_text}

Student's answers so far:
{answers_text}

Correct final answer: {question.correct_answer[:200]}

{"The student says they are stuck and cannot continue." if student_said_stuck else ""}

Identify at which step the student first went wrong or got stuck. If they haven't attempted a step yet, that's where they're stuck.
Return ONLY valid JSON with keys: stuck_at_step (int), reason (str), skill_code (str - use the skill from that step), recommendation (str).
Example: {{"stuck_at_step": 2, "reason": "Divided by wrong term when rearranging", "skill_code": "MATH_ALG_REARRANGE", "recommendation": "Isolate the variable step by step; avoid dividing both sides by an expression containing the unknown."}}
"""
    else:
        # No steps: analyze question + final answer conceptually
        final_answer = answers_by_step.get(1) or ""
        if not final_answer and student_answers and isinstance(student_answers[0], dict):
            final_answer = student_answers[0].get("student_answer", student_answers[0].get("answer", "")) or ""
        prompt = f"""You are a GCSE tutor. A student attempted this {subject_name} question and got it wrong or is stuck.

Question: {question.question_text[:800]}

Correct answer: {question.correct_answer[:200]}

Student's answer: {final_answer}

{"The student says they are stuck." if student_said_stuck else ""}

Identify the main conceptual or procedural error. Return ONLY valid JSON with keys: stuck_at_step (use 1), reason (str), skill_code (str - invent a short code like MATH_ALG_LINEAR), recommendation (str).
Example: {{"stuck_at_step": 1, "reason": "Forgot to expand brackets before collecting terms", "skill_code": "MATH_ALG_EXPAND", "recommendation": "Expand brackets first, then collect like terms."}}
"""

    backend = (getattr(settings, "LLM_BACKEND", "disabled") or "disabled").lower()
    if backend in ("disabled", "none"):
        # Fallback when LLM disabled
        first_skill = steps[0].skill.code if steps else "UNKNOWN"
        return {
            "success": True,
            "stuck_at_step": 1,
            "reason": "LLM diagnostic is disabled. Review the question steps and your working.",
            "skill_code": first_skill,
            "recommendation": f"Focus on {topic_name}. Try the first step again and check each line of working.",
        }

    if backend == "mock":
        return {
            "success": True,
            "stuck_at_step": 1,
            "reason": "Check your working at step 1. Common errors include sign mistakes and wrong operations.",
            "skill_code": "MATH_ALG_LINEAR",
            "recommendation": "Work through each step slowly. Write down what you're doing and why.",
        }

    try:
        from learning.services.llm_service import generate as llm_generate

        raw = llm_generate(prompt=prompt, max_tokens=400, temperature=0.2)
        data = _extract_diagnostic_json(raw)
        if data and isinstance(data, dict):
            return {
                "success": True,
                "stuck_at_step": int(data.get("stuck_at_step", 1)),
                "reason": str(data.get("reason", ""))[:500],
                "skill_code": str(data.get("skill_code", "UNKNOWN"))[:50],
                "recommendation": str(data.get("recommendation", ""))[:500],
            }
    except Exception:
        pass

    # Fallback on parse/LLM error
    first_skill = steps[0].skill.code if steps else "UNKNOWN"
    return {
        "success": True,
        "stuck_at_step": 1,
        "reason": "Unable to analyze. Review your working step by step.",
        "skill_code": first_skill,
        "recommendation": f"Try {topic_name} practice from the beginning. Check each step.",
    }
