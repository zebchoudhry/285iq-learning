import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from learning.models import Lesson, Question, Subject, Topic


@pytest.mark.django_db
def test_lesson_api_sends_the_fields_the_lesson_page_reads():
    subject = Subject.objects.create(name="biology", display_name="Biology")
    topic = Topic.objects.create(subject=subject, name="Cells", order=1)
    lesson = Lesson.objects.create(topic=topic, title="1.1 - Cells", content="x", estimated_duration=45,
                                   focus_areas=["Cell structure"], common_mistakes=["Mixing up plant and animal cells"])
    user = get_user_model().objects.create_user(username="s", password="x-test-pass")
    client = APIClient()
    client.force_authenticate(user)
    data = client.get(f"/api/lesson/{lesson.id}/").data
    assert data["estimated_duration"] == 45 and data["duration"] == 45
    assert data["focus_areas"] == ["Cell structure"]
    assert data["common_mistakes"] == ["Mixing up plant and animal cells"]


@pytest.mark.django_db
def test_fallback_questions_migration_switches_off_only_placeholders():
    from importlib import import_module
    from django.apps import apps

    migration = import_module("learning.migrations.0020_deactivate_fallback_questions")
    subject = Subject.objects.create(name="chemistry", display_name="Chemistry")
    topic = Topic.objects.create(subject=subject, name="Bonding", order=1)
    lesson = Lesson.objects.create(topic=topic, title="2.1 - Ions", content="x")
    junk = Question.objects.create(lesson=lesson, question_text="[Fallback] Bonding: practice question 1",
                                   correct_answer="Sample answer")
    real = Question.objects.create(lesson=lesson, question_text="What is the charge on a sodium ion?",
                                   correct_answer="1+")
    migration.deactivate(apps, None)
    junk.refresh_from_db(); real.refresh_from_db()
    assert not junk.is_active and real.is_active
    migration.reactivate(apps, None)
    junk.refresh_from_db()
    assert junk.is_active
