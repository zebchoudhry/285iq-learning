"""
Build recent activity feed for parent dashboard.
Combines lesson completions and quiz attempts into a unified timeline.
"""
from datetime import timedelta
from collections import defaultdict

from django.utils import timezone

from learning.models import StudentProgress, QuizAttempt


def get_recent_activity(student_id: int, limit: int = 10):
    """
    Return last N study events for the student. One entry per lesson completion
    or aggregated quiz session (per topic per day). Sorted by date descending.
    """
    events = []
    since = timezone.now() - timedelta(days=90)

    # Lesson completions
    for sp in (
        StudentProgress.objects.filter(
            student_id=student_id,
            is_completed=True,
            completion_date__isnull=False,
            completion_date__gte=since,
        )
        .select_related("lesson__topic__subject")
        .order_by("-completion_date")[:limit * 2]
    ):
        if sp.lesson and sp.lesson.topic:
            dt = sp.completion_date
            events.append({
                "type": "lesson_complete",
                "subject": sp.lesson.topic.subject.display_name,
                "subject_id": sp.lesson.topic.subject_id,
                "title": sp.lesson.title,
                "topic": sp.lesson.topic.name,
                "date": dt.date().isoformat() if dt else None,
                "datetime": dt.isoformat() if dt else None,
                "details": f"Completed {sp.lesson.title}",
            })

    # Quiz attempts - aggregate by (topic, date) in Python
    quiz_by_key = defaultdict(lambda: {"total": 0, "correct": 0, "topic_name": "", "subject_name": "", "subject_id": None})
    for qa in (
        QuizAttempt.objects.filter(
            student_id=student_id,
            attempted_at__gte=since,
        )
        .select_related("question__lesson__topic__subject")[:500]
    ):
        if qa.question and qa.question.lesson and qa.question.lesson.topic:
            topic = qa.question.lesson.topic
            key = (topic.id, qa.attempted_at.date() if qa.attempted_at else None)
            if key[1]:
                d = quiz_by_key[key]
                d["total"] += 1
                d["correct"] += 1 if qa.is_correct else 0
                d["topic_name"] = topic.name
                d["subject_name"] = topic.subject.display_name if topic.subject else "Unknown"
                d["subject_id"] = topic.subject_id if topic.subject else None
                d["date"] = key[1].isoformat()

    for (_, _), d in quiz_by_key.items():
        if d["total"] > 0:
            events.append({
                "type": "quiz",
                "subject": d["subject_name"],
                "subject_id": d["subject_id"],
                "title": f"Quiz: {d['topic_name']}",
                "topic": d["topic_name"],
                "date": d.get("date"),
                "details": f"{d['correct']}/{d['total']} correct",
            })

    # Sort by date descending and take limit
    events.sort(key=lambda e: e.get("date") or "1970-01-01", reverse=True)
    return events[:limit]
