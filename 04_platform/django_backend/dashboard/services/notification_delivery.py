"""
Parent notification delivery: rate limiting + email + WhatsApp/SMS + audit log.
Contract: 285IQ Decision & Notification Contract v1.0

WhatsApp/SMS via Twilio (optional — requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
TWILIO_WHATSAPP_FROM env vars). Falls back gracefully to email-only if not configured.
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
    return d - timedelta(days=d.weekday())


def _build_rate_limit_state(student_id: int, current_date: date) -> NotificationRateLimitState:
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


def _send_whatsapp(to_number: str, body: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    Requires env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM.
    Returns True on success, False if Twilio is not configured or call fails.
    """
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', '')

    if not (sid and token and from_number):
        return False

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        # Twilio WhatsApp sandbox format: "whatsapp:+447700900123"
        to = f"whatsapp:{to_number}" if not to_number.startswith('whatsapp:') else to_number
        frm = f"whatsapp:{from_number}" if not from_number.startswith('whatsapp:') else from_number
        client.messages.create(body=body, from_=frm, to=to)
        logger.info("WhatsApp notification sent to %s", to_number)
        return True
    except ImportError:
        logger.debug("twilio package not installed — skipping WhatsApp delivery")
    except Exception:
        logger.warning("WhatsApp send failed to %s", to_number, exc_info=True)
    return False


def _send_sms(to_number: str, body: str) -> bool:
    """
    Send a plain SMS via Twilio (fallback when WhatsApp not available).
    Requires env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SMS_FROM.
    """
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_SMS_FROM', '')

    if not (sid and token and from_number):
        return False

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(body=body, from_=from_number, to=to_number)
        logger.info("SMS notification sent to %s", to_number)
        return True
    except ImportError:
        pass
    except Exception:
        logger.warning("SMS send failed to %s", to_number, exc_info=True)
    return False


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
    parent_phone: str = '',
) -> bool:
    """
    Send a parent notification via email and/or WhatsApp/SMS if rate limits allow.
    Delivery channels tried in order: WhatsApp → SMS → Email.
    Always logs the notification intent; returns True if any channel succeeded.
    """
    current_date = date.today()
    state = _build_rate_limit_state(student_id, current_date)
    priority_enum = (
        NotificationPriority.PRIORITY_1_URGENT if priority == 1
        else NotificationPriority.PRIORITY_2_INFORMATIONAL
    )
    allowed, reason = apply_notification_rate_limits(
        state, str(subject_id), priority_enum, current_date
    )
    if not allowed:
        logger.debug("Notification suppressed for student %s: %s", student_id, reason)
        return False

    subject_line = f"285IQ: {event_type.replace('_', ' ').title()}"
    if subject_display_name:
        subject_line += f" – {subject_display_name}"
    body = message
    if student_name:
        body = f"Student: {student_name}\n\n{body}"
    whatsapp_body = f"285IQ Update 📚\n{subject_line}\n\n{body}"

    # Resolve parent contact details
    resolved_email = parent_email
    resolved_phone = parent_phone
    if not resolved_email or not resolved_phone:
        try:
            from users.models import Student
            student_obj = Student.objects.get(id=student_id)
            if not resolved_email and student_obj.parent_email:
                resolved_email = student_obj.parent_email
            if not resolved_phone and hasattr(student_obj, 'parent_phone') and student_obj.parent_phone:
                resolved_phone = student_obj.parent_phone
        except Exception:
            pass

    sent = False

    # 1. Try WhatsApp first (highest engagement)
    if resolved_phone:
        sent = _send_whatsapp(resolved_phone, whatsapp_body) or sent

    # 2. Try SMS if WhatsApp not configured or failed
    if resolved_phone and not sent:
        sent = _send_sms(resolved_phone, whatsapp_body) or sent

    # 3. Email fallback (always attempt)
    email_recipients = [resolved_email] if resolved_email else None
    if not email_recipients:
        fallback = getattr(settings, 'PARENT_NOTIFICATION_EMAILS', None)
        email_recipients = fallback or [settings.DEFAULT_FROM_EMAIL]

    try:
        send_mail(
            subject=subject_line,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=email_recipients,
            fail_silently=True,
        )
        logger.info(
            "Email notification sent for student %s event '%s' to %s",
            student_id, event_type, email_recipients,
        )
        sent = True
    except Exception:
        logger.warning("Email send failed for student %s", student_id, exc_info=True)

    NotificationLog.objects.create(
        student_id=student_id,
        subject_id=subject_id,
        event_type=event_type,
        priority=priority,
        message=message,
        sent_at=timezone.now(),
    )
    return sent
