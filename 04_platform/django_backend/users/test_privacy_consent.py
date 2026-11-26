import json
import re

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.utils import timezone

from users import parent_consent

pytestmark = pytest.mark.django_db
User = get_user_model()
REGISTER = "/api/users/auth/register/"
PW = "Sturdy-pass-for-tests-7"


def register(client=None, **extra):
    body = {"username": "kid", "email": "kid@example.com", "password": PW, "password_confirm": PW,
            "accept_terms": True, "age_confirmed": True}
    body.update(extra)
    return (client or Client()).post(REGISTER, body, content_type="application/json")


# ---- pages -------------------------------------------------------------------
@pytest.mark.parametrize("path,needle", [("/privacy/", "Privacy notice"), ("/terms/", "Terms of use")])
def test_legal_pages_are_public_and_indexable(path, needle):
    r = Client().get(path, HTTP_HOST="285iq.com")
    assert r.status_code == 200 and needle in r.content.decode()
    assert "X-Robots-Tag" not in r and 'rel="canonical"' in r.content.decode()


def test_privacy_notice_names_the_real_processors_and_rights():
    html = Client().get("/privacy/").content.decode()
    for word in ("Vercel", "Neon", "Brevo", "Stripe", "Google Fonts", "YouTube", "ico.org.uk",
                 "Download my data", "Delete my account", settings.PRIVACY_EMAIL):
        assert word in html, word


def test_operator_is_shown_only_when_configured(settings):
    settings.OPERATOR_NAME = ""
    assert "is run by" not in Client().get("/privacy/").content.decode()
    settings.OPERATOR_NAME = "Test Operator"
    assert "is run by <strong>Test Operator</strong>" in Client().get("/privacy/").content.decode()


def test_footer_links_include_the_legal_pages():
    html = Client().get("/").content.decode()
    assert 'href="/privacy/"' in html and 'href="/terms/"' in html


def test_signup_form_asks_for_consent_and_links_the_policies():
    html = Client().get("/register/").content.decode()
    assert 'id="accept_terms"' in html and 'id="age_confirmed"' in html and 'id="parent_email"' in html
    assert 'href="/privacy/"' in html and 'href="/terms/"' in html


# ---- consent at signup ---------------------------------------------------------
def test_signup_records_when_and_which_terms_were_accepted():
    assert register().status_code == 201
    u = User.objects.get(username="kid")
    assert u.terms_accepted_at and u.terms_version == settings.TERMS_VERSION


@pytest.mark.parametrize("missing", ["accept_terms", "age_confirmed"])
def test_signup_is_refused_without_consent_or_age(missing):
    r = register(**{missing: False})
    assert r.status_code == 400 and missing in r.json()
    assert not User.objects.exists()


def test_signup_is_refused_if_the_consent_fields_are_left_out_entirely():
    body = {"username": "kid", "email": "kid@example.com", "password": PW, "password_confirm": PW}
    assert Client().post(REGISTER, body, content_type="application/json").status_code == 400


def test_parent_email_is_optional():
    assert register().status_code == 201
    assert User.objects.get().parent_email is None


def test_parent_email_cannot_be_the_students_own():
    r = register(parent_email="KID@example.com")
    assert r.status_code == 400 and "parent_email" in r.json()


# ---- parent confirmation --------------------------------------------------------
def test_parent_is_emailed_a_confirmation_and_nothing_else():
    register(parent_email="Parent@Example.com")
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert msg.to == ["parent@example.com"] and "Confirm" in msg.subject
    assert "kid" in msg.body and "Nothing is sent to you until you confirm" in msg.body
    assert str(User.objects.get().parent_access_token) not in msg.body
    assert not User.objects.get().parent_email_verified_at


def link_token():
    return re.search(r"t=(\S+)", mail.outbox[0].body).group(1)


def test_confirming_from_the_link_marks_the_parent_confirmed():
    register(parent_email="parent@example.com")
    token = link_token()
    page = Client().get(f"/parent-confirm/?t={token}")
    assert page.status_code == 200 and b"Yes, I am their parent" in page.content
    assert not User.objects.get().parent_email_verified_at  # opening the page changes nothing
    post = Client().post("/api/users/parent-confirm/", {"token": token}, content_type="application/json")
    assert post.status_code == 200
    assert User.objects.get().parent_email_verified_at


def test_a_bad_link_is_refused():
    assert b"not valid any more" in Client().get("/parent-confirm/?t=garbage").content
    r = Client().post("/api/users/parent-confirm/", {"token": "garbage"}, content_type="application/json")
    assert r.status_code == 400


def test_a_link_stops_working_when_the_parent_email_changes():
    register(parent_email="parent@example.com")
    token = link_token()
    u = User.objects.get()
    u.parent_email = "someone-else@example.com"
    u.save()
    r = Client().post("/api/users/parent-confirm/", {"token": token}, content_type="application/json")
    assert r.status_code == 400


def test_confirm_page_is_not_indexed():
    assert Client().get("/parent-confirm/?t=x")["X-Robots-Tag"] == "noindex, nofollow"


def test_changing_the_parent_email_restarts_confirmation():
    register(parent_email="parent@example.com")
    u = User.objects.get()
    parent_consent.confirm(u)
    mail.outbox.clear()
    c = Client()
    c.force_login(u)
    r = c.post("/api/users/me/parent-email/", {"parent_email": "new@example.com"}, content_type="application/json")
    assert r.status_code == 200 and r.json() == {"parent_email": "new@example.com", "confirmed": False}
    assert len(mail.outbox) == 1 and mail.outbox[0].to == ["new@example.com"]
    cleared = c.post("/api/users/me/parent-email/", {"parent_email": ""}, content_type="application/json")
    assert cleared.json()["parent_email"] == ""


def test_resend_only_when_waiting_for_confirmation():
    register(parent_email="parent@example.com")
    u = User.objects.get()
    c = Client()
    c.force_login(u)
    mail.outbox.clear()
    c.get("/api/users/me/parent-email/?resend=1")
    assert len(mail.outbox) == 1
    parent_consent.confirm(u)
    mail.outbox.clear()
    c.get("/api/users/me/parent-email/?resend=1")
    assert mail.outbox == []


# ---- delete my account ------------------------------------------------------------
def signed_in():
    register()
    u = User.objects.get(username="kid")
    c = Client()
    c.force_login(u)
    return u, c


def delete(c, **body):
    data = {"password": PW, "confirm": "DELETE"}
    data.update(body)
    return c.post("/api/users/auth/delete-account/", data, content_type="application/json")


def test_delete_account_removes_the_user_and_their_data():
    from learning.models import ReadinessSnapshot, Subject

    u, c = signed_in()
    subject = Subject.objects.create(name="biology", display_name="Biology")
    ReadinessSnapshot.objects.create(student=u, subject=subject, taken_on=timezone.now().date(), score=40)
    assert delete(c).status_code == 200
    assert not User.objects.filter(username="kid").exists()
    assert not ReadinessSnapshot.objects.exists()
    assert c.get("/api/users/auth/current-user/").status_code in (401, 403)


def test_delete_needs_the_right_password_and_the_word_delete():
    u, c = signed_in()
    assert delete(c, password="wrong").status_code == 400
    assert delete(c, confirm="nope").status_code == 400
    assert User.objects.filter(username="kid").exists()


def test_delete_requires_sign_in():
    r = Client().post("/api/users/auth/delete-account/", {"password": PW, "confirm": "DELETE"},
                      content_type="application/json")
    assert r.status_code in (401, 403)


# ---- download my data ---------------------------------------------------------------
def test_export_contains_the_users_own_data_and_no_secrets():
    from learning.models import ReadinessSnapshot, Subject

    u, c = signed_in()
    other = User.objects.create_user(username="other", email="other@example.com", password=PW)
    subject = Subject.objects.create(name="biology", display_name="Biology")
    ReadinessSnapshot.objects.create(student=u, subject=subject, taken_on=timezone.now().date(), score=55)
    ReadinessSnapshot.objects.create(student=other, subject=subject, taken_on=timezone.now().date(), score=99)
    r = c.get("/api/users/me/export/")
    assert r.status_code == 200 and "attachment" in r["Content-Disposition"]
    raw = r.content.decode()
    data = json.loads(raw)
    assert data["account"]["username"] == "kid" and data["account"]["email"] == "kid@example.com"
    assert [row["score"] for row in data["readinesssnapshot"]] == [55]
    assert "other@example.com" not in raw and '"score": 99' not in raw
    assert "password" not in data["account"] and "parent_access_token" not in data["account"]
    assert str(u.parent_access_token) not in raw


def test_export_requires_sign_in():
    assert Client().get("/api/users/me/export/").status_code in (401, 403)


def test_settings_page_has_the_privacy_controls():
    u, c = signed_in()
    html = c.get("/settings/").content.decode()
    for needle in ('id="parentForm"', "Download my data", 'id="deleteForm"', 'href="/privacy/"'):
        assert needle in html, needle
