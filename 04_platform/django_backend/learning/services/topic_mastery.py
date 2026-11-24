"""
How well a student currently knows each topic, from their recent answers.

"Recent" means the last RECENT_WINDOW answers in the topic, so mastery moves as the student
improves: a topic stops being treated as weak once they answer it well, not before. A topic is
"graduated" only after enough answers at a high level, so one lucky streak does not retire it.
"""
from typing import Dict, Iterable, Optional

from learning.models import QuizAttempt, Topic
from users.models import StudentTopicPerformance

RECENT_WINDOW = 10
MIN_ATTEMPTS = 3          # below this we do not judge a topic
GRADUATE_ATTEMPTS = 8     # answers needed before a topic can graduate
GRADUATE_ACCURACY = 0.80  # recent accuracy needed to graduate


def topic_mastery(student, topic_ids: Optional[Iterable[int]] = None) -> Dict[int, Dict]:
    """
    topic_id -> {"accuracy": 0..1 or None, "attempts": n, "graduated": bool}
    accuracy is None when the student has not answered enough to judge.
    """
    wanted = list(topic_ids) if topic_ids is not None else list(
        Topic.objects.filter(is_active=True).values_list("id", flat=True)
    )
    results: Dict[int, Dict] = {t: {"accuracy": None, "attempts": 0, "graduated": False} for t in wanted}

    rows = (
        QuizAttempt.objects.filter(student=student, question__lesson__topic_id__in=wanted)
        .order_by("-attempted_at")
        .values_list("question__lesson__topic_id", "is_correct")
    )
    recent: Dict[int, list] = {}
    totals: Dict[int, int] = {}
    for topic_id, ok in rows.iterator():
        totals[topic_id] = totals.get(topic_id, 0) + 1
        bucket = recent.setdefault(topic_id, [])
        if len(bucket) < RECENT_WINDOW:
            bucket.append(bool(ok))

    for topic_id, bucket in recent.items():
        attempts = totals[topic_id]
        if attempts >= MIN_ATTEMPTS:
            accuracy = sum(bucket) / len(bucket)
            half = bucket[: max(1, len(bucket) // 2)]
            graduated = (
                attempts >= GRADUATE_ATTEMPTS
                and accuracy >= GRADUATE_ACCURACY
                and sum(half) / len(half) >= GRADUATE_ACCURACY
            )
            results[topic_id] = {"accuracy": accuracy, "attempts": attempts, "graduated": graduated}
        else:
            results[topic_id]["attempts"] = attempts

    # Older data that only has the aggregate row: use it so existing students are not "untried".
    missing = [t for t, r in results.items() if r["accuracy"] is None]
    if missing:
        for perf in StudentTopicPerformance.objects.filter(
            student=student, topic_id__in=missing, questions_attempted__gte=MIN_ATTEMPTS
        ):
            accuracy = perf.questions_correct / perf.questions_attempted
            results[perf.topic_id] = {
                "accuracy": accuracy,
                "attempts": perf.questions_attempted,
                "graduated": perf.questions_attempted >= GRADUATE_ATTEMPTS and accuracy >= GRADUATE_ACCURACY,
            }
    return results
