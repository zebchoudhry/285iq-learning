"""
Parent confirmation. A student can type any email address as their "parent", so progress emails
go to it only after the owner of that address confirms from a link we email them. Without this a
mistyped or malicious address would receive a child's name and progress.
"""
import logging

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)
SALT = "parent-email-confirmation"
MAX_AGE = 7 * 24 * 60 * 60  # the confirmation link works for 7 days


def make_token(user) -> str:
    return signing.dumps({"u": user.pk, "e": (user.parent_email or "").lower()}, salt=SALT)


def read_token(token: str):
    """Return (user, ok). ok is false if the link is wrong, expired, or the parent email has changed since."""
    from django.contrib.auth import get_user_model

    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE)
        user = get_user_model().objects.get(pk=data["u"])
    except (signing.BadSignature, signing.SignatureExpired, KeyError, get_user_model().DoesNotExist):
        return None, False
    return user, bool(user.parent_email) and user.parent_email.lower() == data.get("e")


def send_confirmation(user) -> bool:
    """Email the parent address a link to confirm. Returns whether it was sent."""
    if not user.parent_email:
        return False
    link = f"{settings.SITE_URL.rstrip('/')}/parent-confirm/?t={make_token(user)}"
    message = (
        "Hello,\n\n"
        f"Someone using the username '{user.username}' on 285IQ, a GCSE revision service, gave this email "
        "address as their parent or carer.\n\n"
        "If that is your child, confirm below so you can get progress updates about their revision. "
        f"Nothing is sent to you until you confirm:\n\n"
        f"{link}\n\n"
        "The link works for 7 days. If you do not know who this is, ignore this email and nothing will be sent. "
        f"To ask us to remove your address, write to {settings.PRIVACY_EMAIL}.\n\n"
        "285IQ"
    )
    try:
        send_mail("Confirm you are a parent on 285IQ", message, settings.DEFAULT_FROM_EMAIL,
                  [user.parent_email], fail_silently=False)
        return True
    except Exception:
        logger.exception("Parent confirmation email for user %s could not be sent", user.pk)
        return False


def confirm(user) -> None:
    user.parent_email_verified_at = timezone.now()
    user.save(update_fields=["parent_email_verified_at"])


def set_parent_email(user, email) -> None:
    """Save a (new) parent email. Verification starts again, and a confirmation email is sent."""
    email = (email or "").strip().lower() or None
    changed = email != (user.parent_email or None)
    user.parent_email = email
    if changed:
        user.parent_email_verified_at = None
    user.save(update_fields=["parent_email", "parent_email_verified_at"])
    if email and changed:
        send_confirmation(user)
