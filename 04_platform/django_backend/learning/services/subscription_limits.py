"""
Free-tier limits and Pro subscription gate.
"""
import functools
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from ..models import QuizAttempt

logger = logging.getLogger(__name__)

FREE_DAILY_ATTEMPT_LIMIT = 10


def get_today_attempt_count(student):
    today = timezone.now().date()
    return QuizAttempt.objects.filter(
        student=student,
        attempted_at__date=today,
    ).count()


def check_free_tier_limits(student):
    """Return 403 Response if free user is over daily limit, else None."""
    if student.is_pro:
        return None
    count = get_today_attempt_count(student)
    if count >= FREE_DAILY_ATTEMPT_LIMIT:
        logger.info("Free-tier daily limit hit for student %s (%d attempts)", student.id, count)
        return Response(
            {"detail": "Daily limit reached. Upgrade to Pro for unlimited practice."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def require_pro(view_func):
    """
    Decorator for DRF @api_view functions: blocks non-Pro students with 403.

    Usage:
        @api_view(['POST'])
        @require_pro
        def my_pro_only_view(request):
            ...
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        student = request.user
        if not student.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        if not getattr(student, 'is_pro', False):
            return Response(
                {"detail": "This feature requires a Pro subscription."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return view_func(request, *args, **kwargs)
    return wrapper
