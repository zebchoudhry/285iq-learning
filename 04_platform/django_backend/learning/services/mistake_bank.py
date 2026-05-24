from datetime import timedelta

from django.utils import timezone

from learning.models import MistakeBankItem, QuestionStep, StruggleEvent


SLOW_START_MS = 45000
SLOW_SUBMIT_MS = 180000


def _skill_from_failed_skill(question, failed_skill):
    skill_code = failed_skill.get("skill_code") if isinstance(failed_skill, dict) else None
    if skill_code:
        step = (
            QuestionStep.objects.filter(question=question, skill__code=skill_code)
            .select_related("skill")
            .first()
        )
        if step:
            return step.skill
    step = QuestionStep.objects.filter(question=question).select_related("skill").order_by("step_order").first()
    return step.skill if step else None


def _mistake_reason(is_correct, wrong_category, time_to_first_action_ms, time_spent_ms, repeated_wrong):
    if repeated_wrong:
        return "repeated_wrong"
    if wrong_category == "guess":
        return "guess"
    if not is_correct:
        return "wrong"
    if time_to_first_action_ms and time_to_first_action_ms >= SLOW_START_MS:
        return "slow"
    if time_spent_ms and time_spent_ms >= SLOW_SUBMIT_MS:
        return "slow"
    return None


def record_attempt_learning_signals(
    *,
    student,
    attempt,
    question,
    raw_answer,
    is_correct,
    wrong_category,
    failed_skill,
    remediation_tip,
    confidence_level="",
):
    """
    Persist durable learning signals from an attempt.

    This keeps the product loop centred on mistakes: wrong, guessed, repeated,
    or unusually slow answers become reviewable items and diagnostic events.
    """
    time_to_first_action_ms = attempt.time_to_first_action_ms
    time_spent_ms = attempt.time_spent_ms
    repeated_wrong = bool(getattr(attempt, "needs_review", False))
    reason = _mistake_reason(
        is_correct=is_correct,
        wrong_category=wrong_category,
        time_to_first_action_ms=time_to_first_action_ms,
        time_spent_ms=time_spent_ms,
        repeated_wrong=repeated_wrong,
    )
    if reason is None:
        return None

    topic = question.lesson.topic
    skill = _skill_from_failed_skill(question, failed_skill)
    next_review_at = timezone.now() + timedelta(days=1 if not is_correct else 3)

    item, created = MistakeBankItem.objects.get_or_create(
        student=student,
        question=question,
        defaults={
            "topic": topic,
            "skill": skill,
            "reason": reason,
            "wrong_category": wrong_category or "",
            "last_student_answer": raw_answer or "",
            "remediation_tip": remediation_tip or "",
            "next_review_at": next_review_at,
        },
    )
    if not created:
        item.topic = topic
        item.skill = skill or item.skill
        item.reason = reason
        item.wrong_category = wrong_category or item.wrong_category
        item.last_student_answer = raw_answer or item.last_student_answer
        item.remediation_tip = remediation_tip or item.remediation_tip
        item.attempts_count += 1
        item.next_review_at = next_review_at
        if is_correct:
            item.correct_retries += 1
            if item.correct_retries >= 2:
                item.status = "mastered"
            else:
                item.status = "retrying"
        else:
            item.correct_retries = 0
            item.status = "active"
        item.save()

    trigger = "wrong_answer"
    if repeated_wrong:
        trigger = "repeated_wrong"
    elif reason == "slow":
        trigger = "slow_start" if time_to_first_action_ms and time_to_first_action_ms >= SLOW_START_MS else "slow_submit"

    event = StruggleEvent.objects.create(
        student=student,
        question=question,
        topic=topic,
        skill=skill,
        quiz_attempt=attempt,
        trigger=trigger,
        stuck_point=(failed_skill or {}).get("skill_code", "") if isinstance(failed_skill, dict) else "",
        mistake_type=wrong_category or "",
        confidence_level=confidence_level or "",
        time_to_first_action_ms=time_to_first_action_ms,
        time_spent_ms=time_spent_ms,
        student_answer=raw_answer or "",
        diagnostic_message=remediation_tip or "",
        recommended_intervention="retry_similar" if is_correct else "hint",
    )
    return {"mistake": item, "event": event}
