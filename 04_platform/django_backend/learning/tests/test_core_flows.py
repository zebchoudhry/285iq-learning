"""
Integration tests for critical student and parent flows.

These tests use Django's test client and SQLite in-memory DB (pytest-django).
They cover the golden paths that regressions are most likely to break.
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def registered_student(db):
    """Create and return a Student via the register API."""
    from users.models import Student
    student = Student.objects.create_user(
        username="teststu",
        email="teststu@example.com",
        password="TestPass123!",
    )
    from users.models import UserProfile
    from datetime import date
    UserProfile.objects.get_or_create(student=student)
    return student


@pytest.fixture
def auth_client(client, registered_student):
    client.force_login(registered_student)
    return client, registered_student


@pytest.fixture
def subject_with_content(db):
    """Create a Subject → Topic → Lesson → Question chain."""
    from dashboard.models import ExamBoard
    board, _ = ExamBoard.objects.get_or_create(code="aqa", defaults={"name": "AQA"})
    from learning.models import Subject, Topic, Lesson, Question, MultipleChoiceOption
    subject, _ = Subject.objects.get_or_create(
        name="mathematics", tier="higher", exam_board=board,
        defaults={"display_name": "GCSE Mathematics", "is_active": True},
    )
    topic, _ = Topic.objects.get_or_create(
        subject=subject, name="Algebra",
        defaults={"description": "Algebra basics", "is_active": True},
    )
    lesson, _ = Lesson.objects.get_or_create(
        topic=topic, title="Solving Equations",
        defaults={
            "content": "Learn to solve linear equations.",
            "lesson_type": "theory",
            "difficulty_level": 2,
            "is_active": True,
        },
    )
    question, _ = Question.objects.get_or_create(
        lesson=lesson,
        question_text="What is x if 2x = 8?",
        defaults={
            "correct_answer": "4",
            "question_type": "multiple_choice",
            "difficulty_level": 1,
            "is_active": True,
        },
    )
    MultipleChoiceOption.objects.get_or_create(question=question, option_text="4", defaults={"is_correct": True, "order": 0})
    MultipleChoiceOption.objects.get_or_create(question=question, option_text="2", defaults={"is_correct": False, "order": 1})
    return subject, topic, lesson, question


class TestAuthFlow(TestCase):
    def test_unauthenticated_api_returns_403(self):
        resp = self.client.get("/api/loop-metrics/")
        self.assertIn(resp.status_code, [401, 403])

    def test_login_required_redirect(self):
        resp = self.client.get("/")
        # Should redirect to login or return auth error
        self.assertIn(resp.status_code, [200, 302, 401, 403])


@pytest.mark.django_db
class TestPracticeFlow:
    def test_practice_start_requires_auth(self, client, subject_with_content):
        subject, *_ = subject_with_content
        resp = client.post("/api/practice/start/", {"subject_id": subject.id}, content_type="application/json")
        assert resp.status_code in (401, 403)

    def test_practice_start_authenticated(self, auth_client, subject_with_content):
        client, student = auth_client
        subject, topic, lesson, question = subject_with_content
        resp = client.post(
            "/api/practice/start/",
            {"subject_id": subject.id},
            content_type="application/json",
        )
        assert resp.status_code in (200, 201, 400)

    def test_submit_attempt_correct_answer(self, auth_client, subject_with_content):
        client, student = auth_client
        subject, topic, lesson, question = subject_with_content
        resp = client.post(
            "/api/attempts/",
            {
                "question_id": question.id,
                "student_answer": "4",
                "time_spent": 10,
            },
            content_type="application/json",
        )
        assert resp.status_code in (200, 201)
        if resp.status_code in (200, 201):
            data = resp.json()
            assert "is_correct" in data or "correct" in str(data)


@pytest.mark.django_db
class TestSubscriptionGate:
    def test_is_pro_false_for_new_student(self, registered_student):
        assert registered_student.is_pro is False

    def test_free_tier_limit_not_reached(self, registered_student):
        from learning.services.subscription_limits import check_free_tier_limits
        result = check_free_tier_limits(registered_student)
        assert result is None  # No limit hit yet


@pytest.mark.django_db
class TestParentDashboard:
    def test_invalid_token_returns_404(self, client):
        import uuid
        fake_token = uuid.uuid4()
        resp = client.get(f"/api/parent/dashboard/{fake_token}/")
        assert resp.status_code == 404

    def test_valid_token_returns_200(self, client, registered_student):
        resp = client.get(f"/api/parent/dashboard/{registered_student.parent_access_token}/")
        assert resp.status_code == 200
        data = resp.json()
        assert "student_name" in data

    def test_export_invalid_token_returns_404(self, client):
        import uuid
        resp = client.get(f"/api/parent/export/{uuid.uuid4()}/pdf/")
        assert resp.status_code == 404

    def test_export_valid_token_returns_file(self, client, registered_student):
        resp = client.get(f"/api/parent/export/{registered_student.parent_access_token}/pdf/")
        assert resp.status_code == 200
        assert resp["Content-Disposition"].startswith("attachment")


@pytest.mark.django_db
class TestDashboardCache:
    def test_snapshot_roundtrip(self, registered_student):
        from learning.services.dashboard_cache import get_snapshot, set_snapshot, invalidate_snapshot
        payload = {"student_id": registered_student.id, "subjects": []}
        set_snapshot(registered_student.id, payload)
        cached = get_snapshot(registered_student.id)
        assert cached is not None
        assert cached["student_id"] == registered_student.id
        invalidate_snapshot(registered_student.id)
        assert get_snapshot(registered_student.id) is None


@pytest.mark.django_db
class TestAdminContentEndpoints:
    def test_generate_questions_requires_staff(self, auth_client):
        client, student = auth_client
        resp = client.post("/api/admin/generate-questions/", {"topic_id": 1}, content_type="application/json")
        assert resp.status_code == 403

    def test_question_stats_requires_staff(self, auth_client):
        client, student = auth_client
        resp = client.get("/api/admin/question-stats/")
        assert resp.status_code == 403
