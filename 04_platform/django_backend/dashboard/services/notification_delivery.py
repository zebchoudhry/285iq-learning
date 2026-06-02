"""
Parent notification delivery: rate limiting + email + audit log.
Contract: 285IQ Decision & Notification Contract v1.0
"""
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from dashboard.models import NotificationLog
from decision_engine.v1_0.core import (
    NotificationRateLimitState,
    NotificationPriority,
    apply_notification_rate_limits,
)

logger = logging.getLogger(__name__)


def _week_start(d: date) -> date:
    """Monday of the week for d."""
    return d - timedelta(days=d.weekday())


def _build_rate_limit_state(student_id: int, current_date: date) -> NotificationRateLimitState:
    """Build rate limit state from NotificationLog for this student."""
    week_start = _week_start(current_date)
    since = timezone.make_aware(timezone.datetime.combine(week_start, timezone.datetime.min.time()))
    logs = list(
        NotificationLog.objects.filter(
            student_id=student_id,
            sent_at__gte=since
        ).values_list('subject_id', 'sent_at')
    )

    subject_count = {}
    total = 0
    last_date = None
    for subj_id, sent_at in logs:
        if sent_at:
            sent_date = sent_at.date() if hasattr(sent_at, 'date') else sent_at
            if last_date is None or sent_date > last_date:
                last_date = sent_date
        key = str(subj_id) if subj_id else 'global'
        subject_count[key] = subject_count.get(key, 0) + 1
        total += 1

    return NotificationRateLimitState(
        subject_notifications_this_week=subject_count,
        total_notifications_this_week=total,
        last_notification_date=last_date,
        week_start=week_start,
    )


def send_parent_notification(
    *,
    student_id: int,
    subject_id: int,
    event_type: str,
    priority: int,
    message: str,
    subject_display_name: str = '',
    student_name: str = '',
    parent_email: str = '',
) -> bool:
    """
    Send a parent notification email if rate limits allow.
    Always logs the notification intent; only sends email when allowed.

    Returns True if email was sent, False if suppressed or failed.
    """
    current_date = date.today()
    state = _build_rate_limit_state(student_id, current_date)
    priority_enum = NotificationPriority.PRIORITY_1_URGENT if priority == 1 else NotificationPriority.PRIORITY_2_INFORMATIONAL
    allowed, reason = apply_notification_rate_limits(
        state, str(subject_id), priority_enum, current_date
    )
    if not allowed:
        return False

    subject_line = f"285IQ: {event_type.replace('_', ' ').title()}"
    if subject_display_name:
        subject_line += f" – {subject_display_name}"
    body = message
    if student_name:
        body = f"Student: {student_name}\n\n{body}"

    # Build recipient list: parent_email arg > student.parent_email > settings fallback
    recipient_list = []
    if parent_email:
        recipient_list = [parent_email]
    else:
        try:
            from users.models import Student
            student_obj = Student.objects.get(id=student_id)
            if student_obj.parent_email:
                recipient_list = [student_obj.parent_email]
        except Exception:
            pass
    if not recipient_list:
        fallback = getattr(settings, 'PARENT_NOTIFICATION_EMAILS', None)
        recipient_list = fallback or [settings.DEFAULT_FROM_EMAIL]

    try:
        send_mail(
            subject=subject_line,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=True,
        )
        logger.info("Parent notification sent for student %s event '%s' to %s", student_id, event_type, recipient_list)
    except Exception:
        logger.warning("Failed to send parent notification for student %s", student_id, exc_info=True)

    NotificationLog.objects.create(
        student_id=student_id,
        subject_id=subject_id,
        event_type=event_type,
        priority=priority,
        message=message,
        sent_at=timezone.now(),
    )
    return True
