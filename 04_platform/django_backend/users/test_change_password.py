import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client

pytestmark = pytest.mark.django_db
User = get_user_model()
URL = "/api/users/auth/change-password/"
OLD = "Old-pass-for-tests-1"
NEW = "Brand-new-pass-for-tests-2"


@pytest.fixture(autouse=True)
def clear_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    return User.objects.create_user(username="kid", email="kid@example.com", password=OLD)


@pytest.fixture
def client(user):
    c = Client()
    c.force_login(user)
    return c


def post(client, **data):
    body = {"current_password": OLD, "new_password": NEW, "new_password_confirm": NEW}
    body.update(data)
    return client.post(URL, body, content_type="application/json")


def test_changes_the_password_and_keeps_this_session(client, user):
    r = post(client)
    assert r.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW) and not user.check_password(OLD)
    assert client.get("/api/users/auth/current-user/").status_code == 200  # still signed in here


def test_other_sessions_are_signed_out(user):
    other = Client()
    other.force_login(user)
    mine = Client()
    mine.force_login(user)
    assert post(mine).status_code == 200
    assert other.get("/api/users/auth/current-user/").status_code in (401, 403)


def test_new_password_works_for_login(client, user):
    post(client)
    assert Client().login(username="kid", password=NEW)
    assert not Client().login(username="kid", password=OLD)


def test_wrong_current_password_is_rejected(client, user):
    r = post(client, current_password="not-it")
    assert r.status_code == 400 and "current_password" in r.json()
    user.refresh_from_db()
    assert user.check_password(OLD)


def test_new_passwords_must_match(client):
    r = post(client, new_password_confirm=NEW + "x")
    assert r.status_code == 400 and "new_password_confirm" in r.json()


@pytest.mark.parametrize("weak", ["short1", "12345678901", "password123", "qwerty123"])
def test_weak_new_passwords_are_rejected_with_a_reason(client, weak):
    r = post(client, new_password=weak, new_password_confirm=weak)
    assert r.status_code == 400 and r.json()["new_password"]


def test_new_password_must_differ_from_current(client):
    r = post(client, new_password=OLD, new_password_confirm=OLD)
    assert r.status_code == 400 and "new_password" in r.json()


def test_requires_sign_in():
    r = Client().post(URL, {"current_password": OLD, "new_password": NEW, "new_password_confirm": NEW},
                      content_type="application/json")
    assert r.status_code in (401, 403)


def test_guessing_is_slowed_down(client):
    codes = [post(client, current_password=f"guess-{i}").status_code for i in range(12)]
    assert codes[:10] == [400] * 10 and codes[-1] == 429


def test_settings_page_shows_the_form_and_sets_csrf_cookie(client):
    r = client.get("/settings/")
    assert r.status_code == 200
    html = r.content.decode()
    assert 'id="pwForm"' in html and 'autocomplete="current-password"' in html and 'autocomplete="new-password"' in html
    assert "csrftoken" in r.cookies
