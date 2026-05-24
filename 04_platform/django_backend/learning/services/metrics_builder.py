from django.db.models import Avg, Count
from learning.models import QuizAttempt


def build_topic_metrics(student_id: int, topic_id: int) -> dict:
    """
    Collects and normalises metrics for a student-topic pair.
    Returns a plain dict for the decision engine.
    """

    attempts = QuizAttempt.objects.filter(
        student_id=student_id,
        question__lesson__topic_id=topic_id
    ).order_by("-attempted_at")

    total_attempts = attempts.count()

    if total_attempts == 0:
        return {
            "total_attempts": 0
        }

    correct_count = attempts.filter(is_correct=True).count()
    accuracy_rate = (correct_count / total_attempts) * 100

    recent_attempts = attempts[:10]
    recent_correct = recent_attempts.filter(is_correct=True).count()
    recent_accuracy = (recent_correct / max(len(recent_attempts), 1)) * 100

    # Error breakdown
    error_counts = attempts.values("error_type").annotate(c=Count("id"))
    dominant_error = "none"
    conceptual_errors = 0

    for row in error_counts:
        if row["error_type"] == "conceptual":
            conceptual_errors = row["c"]
        if row["c"] > total_attempts * 0.4:
            dominant_error = row["error_type"]

    conceptual_error_rate = (conceptual_errors / total_attempts) * 100

    avg_time_spent = attempts.aggregate(
        avg_time=Avg("time_spent_ms")
    )["avg_time"] or 0

    repeated_same_error = (
        attempts.values("error_type")
        .annotate(c=Count("id"))
        .filter(c__gte=3)
        .count()
    )

    return {
        "total_attempts": total_attempts,
        "accuracy_rate": accuracy_rate,
        "recent_accuracy": recent_accuracy,
        "accuracy_drop": 0,  # placeholder (can be improved later)
        "conceptual_error_rate": conceptual_error_rate,
        "repeated_same_error": repeated_same_error,
        "avg_time_spent_ms": avg_time_spent,
        "time_to_first_action_ms": 0,  # optional later
        "response_time_trend": "stable",
        "dominant_error_type": dominant_error,
        "previous_mode": None,  # filled later
        "consistent_over_days": False,
        "exam_time_threshold_ms": 90000,
        "exam_average_time_ms": 60000,
    }
