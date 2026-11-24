"""
Exam progress: how ready is the student, how long is left, and are they on pace?

Rule-based on purpose. A learning model needs far more answers per student than we will have
for a long time; the readiness snapshots stored here are the history a model could be trained on
later. Everything shown to the student is labelled as an estimate.
"""
import math
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone

from learning.models import ReadinessSnapshot, StudentExamSettings, Subject, Topic
from learning.services.exam_readiness import build_subject_exam_readiness
from learning.services.topic_mastery import topic_mastery

READY_TARGET = 85          # the score at which a subject counts as exam ready
DEFAULT_POINTS_PER_WEEK = 2.0
RATE_LOOKBACK_DAYS = 28
MAX_SESSIONS_PER_WEEK = 7


def record_snapshot(student, subject, readiness: Optional[Dict[str, Any]] = None) -> ReadinessSnapshot:
    """Store today's readiness for the student and subject (once a day; later calls update it)."""
    readiness = readiness or build_subject_exam_readiness(student, subject)
    topic_ids = list(Topic.objects.filter(subject=subject, is_active=True).values_list("id", flat=True))
    mastery = topic_mastery(student, topic_ids)
    m = readiness["metrics"]
    snap, _ = ReadinessSnapshot.objects.update_or_create(
        student=student, subject=subject, taken_on=timezone.now().date(),
        defaults={
            "score": readiness["score"],
            "recent_accuracy": m["recent_accuracy"],
            "coverage": m["coverage_score"],
            "active_mistakes": m["active_mistakes"],
            "sessions_7d": m["sessions_last_7_days"],
            "topic_mastery": {
                str(t): (round(v["accuracy"] * 100) if v["accuracy"] is not None else None)
                for t, v in mastery.items()
            },
        },
    )
    return snap


def _points_per_week(student, subject, today: date) -> Optional[float]:
    """Measured improvement rate from the last four weeks of snapshots, or None if too little data."""
    rows = list(
        ReadinessSnapshot.objects.filter(
            student=student, subject=subject, taken_on__gte=today - timedelta(days=RATE_LOOKBACK_DAYS)
        ).order_by("taken_on")
    )
    if len(rows) < 2:
        return None
    days = (rows[-1].taken_on - rows[0].taken_on).days
    if days < 7:
        return None
    return (rows[-1].score - rows[0].score) / (days / 7.0)


def _history(student, subject, limit: int = 60) -> List[Dict[str, Any]]:
    rows = ReadinessSnapshot.objects.filter(student=student, subject=subject).order_by("-taken_on")[:limit]
    return [{"date": r.taken_on.isoformat(), "score": r.score} for r in reversed(list(rows))]


def build_subject_progress(student, setting: StudentExamSettings, today: Optional[date] = None) -> Dict[str, Any]:
    today = today or timezone.now().date()
    subject = setting.subject
    readiness = build_subject_exam_readiness(student, subject)
    snapshot = record_snapshot(student, subject, readiness)
    score = readiness["score"]

    days_left = (setting.exam_date - today).days
    weeks_left = max(days_left, 0) / 7.0
    measured = _points_per_week(student, subject, today)
    rate = measured if measured is not None else DEFAULT_POINTS_PER_WEEK
    projected = max(0, min(100, round(score + rate * weeks_left)))

    if days_left < 0:
        state = "exam_passed"
    elif score >= READY_TARGET:
        state = "ready"
    elif projected >= READY_TARGET:
        state = "on_track"
    else:
        state = "behind"

    sessions_needed = None
    if state in ("on_track", "behind") and weeks_left > 0:
        sessions_7d = max(readiness["metrics"]["sessions_last_7_days"], 0)
        points_per_session = (rate / sessions_7d) if (measured and measured > 0 and sessions_7d) else 3.0
        points_per_session = max(points_per_session, 0.5)
        needed = (READY_TARGET - score) / (weeks_left * points_per_session)
        sessions_needed = max(1, min(MAX_SESSIONS_PER_WEEK, math.ceil(needed)))

    first = ReadinessSnapshot.objects.filter(student=student, subject=subject).order_by("taken_on").first()
    return {
        "subject_id": subject.id,
        "subject": subject.display_name,
        "exam_date": setting.exam_date.isoformat(),
        "exam_month": setting.exam_date.strftime("%B %Y"),
        "days_left": days_left,
        "weeks_left": round(weeks_left, 1),
        "score": score,
        "target": READY_TARGET,
        "percent_of_target": min(100, round(100 * score / READY_TARGET)),
        "start_score": first.score if first else score,
        "projected_score": projected,
        "points_per_week": round(rate, 1),
        "rate_is_measured": measured is not None,
        "state": state,
        "sessions_per_week_needed": sessions_needed,
        "sessions_last_7_days": readiness["metrics"]["sessions_last_7_days"],
        "target_grade": readiness["target_grade"],
        "predicted_grade": readiness["predicted_grade"],
        "history": _history(student, subject),
        "snapshot_id": snapshot.id,
    }


def build_exam_progress(student, today: Optional[date] = None) -> Dict[str, Any]:
    settings_qs = (
        StudentExamSettings.objects.filter(student=student, subject__is_active=True)
        .select_related("subject")
        .order_by("exam_date")
    )
    subjects = [build_subject_progress(student, s, today) for s in settings_qs]
    upcoming = [s for s in subjects if s["days_left"] >= 0]
    return {
        "has_exam_dates": bool(subjects),
        "subjects": subjects,
        "next_exam": min(upcoming, key=lambda s: s["days_left"]) if upcoming else None,
    }
