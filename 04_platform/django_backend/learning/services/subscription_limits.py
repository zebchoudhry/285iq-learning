"""
Free-tier limits for quiz attempts (submit_attempt only).
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from ..models import QuizAttempt


def get_today_attempt_count(student):
    """Count QuizAttempt rows for student on the current calendar day (UTC)."""
    today = timezone.now().date()
    return QuizAttempt.objects.filter(
        student=student,
        attempted_at__date=today,
    ).count()


def check_free_tier_limits(student):
    """
    If not Pro and already at 10+ attempts today, return 403 Response.
    Otherwise return None (allow).
    """
    if student.is_pro:
        return None
    if get_today_attempt_count(student) >= 10:
        return Response(
            {
                "detail": "Daily limit reached. Upgrade to Pro for unlimited practice.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    return None
