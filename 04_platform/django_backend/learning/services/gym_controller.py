from django.db.models import Count
from django.utils import timezone

from learning.models import QuizAttempt, StudentGymState, Topic
from learning.services.decision_engine_v2 import decide_gym_mode as decide_gym_mode_stateless
from learning.services.gym_mode_memory import apply_hysteresis
from learning.services.content_router import select_content_for_mode
from learning.services.exam_board_scope import resolve_exam_board_id_for_student_subject


def decide_gym_mode(student_id: int, topic_id: int, use_llm: bool = False) -> dict:
    """
    Stateful gym-mode decision.
    Combines live performance metrics + hysteresis memory + content routing.
    """

    attempts = QuizAttempt.objects.filter(
        student_id=student_id,
        question__lesson__topic_id=topic_id
    ).order_by("-attempted_at")

    total_attempts = attempts.count()

    if total_attempts == 0:
        metrics = {
            "total_attempts": 0,
            "accuracy_rate": 0,
            "recent_accuracy": 0,
            "dominant_error_type": "none",
            "days_since_last_attempt": None,
        }
    else:
        correct = attempts.filter(is_correct=True).count()
        accuracy = correct / total_attempts

        recent = attempts[:5]
        recent_correct = recent.filter(is_correct=True).count()
        recent_accuracy = recent_correct / max(recent.count(), 1)

        agg = (
            attempts.exclude(error_type="none")
            .values("error_type")
            .annotate(c=Count("id"))
            .order_by("-c")
            .first()
        )
        dominant_error = agg["error_type"] if agg else "none"

        last = attempts.first()
        if last and last.attempted_at:
            delta = timezone.now() - last.attempted_at
            days_since = max(0, delta.days)
        else:
            days_since = 0

        metrics = {
            "total_attempts": total_attempts,
            "accuracy_rate": accuracy,
            "recent_accuracy": recent_accuracy,
            "dominant_error_type": dominant_error,
            "days_since_last_attempt": days_since,
        }

    proposed_mode, reason, snapshot = decide_gym_mode_stateless(metrics)

    state = StudentGymState.objects.filter(
        student_id=student_id,
        topic_id=topic_id
    ).first()

    final_mode, confirmations = apply_hysteresis(
        proposed_mode=proposed_mode,
        state=state,
    )

    if state is None:
        StudentGymState.objects.create(
            student_id=student_id,
            topic_id=topic_id,
            current_mode=final_mode,
            confirmation_count=confirmations,
        )
    else:
        state.current_mode = final_mode
        state.confirmation_count = confirmations
        state.save(update_fields=["current_mode", "confirmation_count", "updated_at"])

    topic = Topic.objects.filter(id=topic_id).select_related("subject").first()
    exam_board_id = None
    if topic:
        exam_board_id = resolve_exam_board_id_for_student_subject(
            student_id, topic.subject_id
        )

    content = select_content_for_mode(
        mode=final_mode,
        student_id=student_id,
        topic_id=topic_id,
        use_llm=use_llm,
        exam_board_id=exam_board_id,
    )

    return {
        "mode": final_mode,
        "reason": reason,
        "metrics_snapshot": snapshot,
        "confirmations": confirmations,
        "content": content,
    }
