import re

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, override_settings

pytestmark = pytest.mark.django_db
User = get_user_model()
REQUEST = "/api/users/auth/password-reset/"
CONFIRM = "/api/users/auth/password-reset/confirm/"
NEW = "Fresh-pass-for-tests-9"


class BrokenBackend:
    """An email backend that always fails, like a mail server that is down or a wrong key."""

    def __init__(self, *args, **kwargs):
        pass

    def open(self):
        return True

    def close(self):
        pass

    def send_messages(self, messages):
        raise ConnectionError("mail server unreachable")


@pytest.fixture
def user():
    return User.objects.create_user(username="kid", email="kid@example.com", password="Old-pass-for-tests-1",
                                    first_name="Sam")


def ask(email="kid@example.com", **extra):
    return Client().post(REQUEST, {"email": email}, content_type="application/json", **extra)


def test_reset_email_is_sent_with_a_link_to_the_real_site(user):
    r = ask()
    assert r.status_code == 200
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == ["kid@example.com"] and msg.subject == "Reset your 285IQ password"
    assert msg.from_email == settings.DEFAULT_FROM_EMAIL
    assert "Hi Sam" in msg.body and "24 hours" in msg.body
    link = re.search(r"https?://\S+", msg.body).group(0)
    assert link.startswith(settings.SITE_URL.rstrip("/") + "/reset-password/?uid=")


@override_settings(ALLOWED_HOSTS=["*"])
def test_forged_host_header_does_not_change_the_link(user):
    ask(HTTP_HOST="evil.example")
    assert "evil.example" not in mail.outbox[0].body


def test_email_case_does_not_matter(user):
    ask("KID@Example.com")
    assert len(mail.outbox) == 1


def test_unknown_email_gets_the_same_answer_and_no_email(user):
    known, unknown = ask(), ask("nobody@example.com")
    assert known.json() == unknown.json() and unknown.status_code == 200
    assert len(mail.outbox) == 1  # only the known address got one


def test_the_link_in_the_email_resets_the_password_once(user):
    ask()
    link = re.search(r"https?://\S+", mail.outbox[0].body).group(0)
    uid = re.search(r"uid=([^&]+)", link).group(1)
    token = re.search(r"token=(\S+)", link).group(1)
    body = {"uid": uid, "token": token, "new_password": NEW, "new_password_confirm": NEW}
    assert Client().post(CONFIRM, body, content_type="application/json").status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW)
    # the same link cannot be used again, because the password it was made for has changed
    assert Client().post(CONFIRM, body, content_type="application/json").status_code == 400


@override_settings(EMAIL_BACKEND="users.test_password_reset_email.BrokenBackend")
def test_mail_failure_is_logged_but_the_answer_does_not_change(user, caplog):
    r = ask()
    assert r.status_code == 200
    assert "could not be sent" in caplog.text


def test_reset_links_last_24_hours():
    assert settings.PASSWORD_RESET_TIMEOUT == 24 * 60 * 60
    assert settings.EMAIL_TIMEOUT > 0
