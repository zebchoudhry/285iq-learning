"""
Record study activity for parent dashboard and decision engine.
One StudySession per calendar day per (student, subject) - updates existing when same day.
"""
from django.utils import timezone
from datetime import datetime

from learning.models import StudySession


def record_study_activity(
    *,
    student,
    subject,
    topic=None,
    duration_seconds: int = 0,
    questions_attempted: int = 0,
    questions_correct: int = 0,
):
    """
    Record or update a StudySession for today. One session per day per (student, subject).
    Multiple lesson completions or quiz attempts on the same day aggregate into one record.
    """
    today = timezone.now().date()
    try:
        session = StudySession.objects.filter(
            student=student,
            subject=subject,
            started_at__date=today,
        ).first()

        if session:
            session.duration_seconds = (session.duration_seconds or 0) + duration_seconds
            session.questions_attempted = (session.questions_attempted or 0) + questions_attempted
            session.questions_correct = (session.questions_correct or 0) + questions_correct
            if topic and not session.topic_id:
                session.topic = topic
            session.save()
        else:
            StudySession.objects.create(
                student=student,
                subject=subject,
                topic=topic,
                duration_seconds=duration_seconds,
                questions_attempted=questions_attempted,
                questions_correct=questions_correct,
            )
    except Exception:
        pass  # Best-effort; don't break the main flow
