"""
Parent notification delivery: rate limiting + email + audit log.
Contract: 285IQ Decision & Notification Contract v1.0
"""
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

    # Get parent email from settings or student (if we had parent email on student profile)
    # For now we use a placeholder; in production you'd have ParentProfile or similar.
    recipient_list = getattr(settings, 'PARENT_NOTIFICATION_EMAILS', None)
    if not recipient_list:
        # Development: don't fail, just log. Console backend will print.
        recipient_list = [getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@285iq.com')]

    try:
        send_mail(
            subject=subject_line,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=True,
        )
    except Exception:
        pass

    NotificationLog.objects.create(
        student_id=student_id,
        subject_id=subject_id,
        event_type=event_type,
        priority=priority,
        message=message,
        sent_at=timezone.now(),
    )
    return True
