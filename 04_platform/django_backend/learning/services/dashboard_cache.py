"""
Simple DB-backed snapshot cache for parent dashboard responses.

The full evaluation (decision engine + narrative) is expensive for multi-subject
students. We cache the serialised response dict and serve it stale while
refreshing on first access after TTL expires.
"""
import json
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

_CACHE_MODEL = None


def _model():
    global _CACHE_MODEL
    if _CACHE_MODEL is None:
        from learning.models import ParentDashboardSnapshot
        _CACHE_MODEL = ParentDashboardSnapshot
    return _CACHE_MODEL


def get_snapshot(student_id: int):
    """Return cached payload dict if fresh, else None."""
    from django.conf import settings
    ttl = getattr(settings, 'PARENT_DASHBOARD_CACHE_TTL', 3600)
    try:
        snap = _model().objects.get(student_id=student_id)
        age = (timezone.now() - snap.generated_at).total_seconds()
        if age < ttl:
            return json.loads(snap.payload)
        logger.debug("Dashboard cache stale for student %s (age %.0fs)", student_id, age)
    except Exception:
        pass
    return None


def set_snapshot(student_id: int, payload: dict):
    """Persist payload dict as snapshot."""
    try:
        _model().objects.update_or_create(
            student_id=student_id,
            defaults={
                'payload': json.dumps(payload, default=str),
                'generated_at': timezone.now(),
            },
        )
    except Exception:
        logger.warning("Failed to write dashboard cache for student %s", student_id, exc_info=True)


def invalidate_snapshot(student_id: int):
    """Remove cached snapshot so next request recalculates."""
    try:
        _model().objects.filter(student_id=student_id).delete()
    except Exception:
        pass
