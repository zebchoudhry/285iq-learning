import pytest
from io import StringIO

from django.core.management import call_command

from learning.models import Lesson, Question, Subject, Topic
from learning.management.commands import restore_question_dedupe as cmd

pytestmark = pytest.mark.django_db


def make(subject_name, text, active):
    subject, _ = Subject.objects.get_or_create(name=subject_name, defaults={"display_name": subject_name})
    topic, _ = Topic.objects.get_or_create(subject=subject, name="T", defaults={"order": 1})
    lesson, _ = Lesson.objects.get_or_create(topic=topic, title="1.1 - L", defaults={"content": "x"})
    return Question.objects.create(lesson=lesson, question_text=text, correct_answer="a",
                                   question_type="short_answer", is_active=active)


def test_report_only_by_default_and_refuses_on_mismatch(monkeypatch):
    q = make("physics", "Copy?", False)
    out = StringIO()
    call_command("restore_question_dedupe", stdout=out)
    assert "Report only" in out.getvalue()
    call_command("restore_question_dedupe", "--apply", stdout=StringIO(), stderr=StringIO())
    q.refresh_from_db()
    assert q.is_active is False  # checksum does not match a 1-row test db


def test_restores_exactly_the_hidden_set_when_checksum_matches(monkeypatch):
    hidden = make("mathematics", "Copy?", False)
    placeholder = make("mathematics", "[Fallback] Algebra: practice question 1", False)
    chem = make("chemistry", "Other subject?", False)
    monkeypatch.setattr(cmd, "EXPECTED_COUNT", 1)
    monkeypatch.setattr(cmd, "EXPECTED_SUM", hidden.id)
    call_command("restore_question_dedupe", "--apply", stdout=StringIO())
    for q in (hidden, placeholder, chem):
        q.refresh_from_db()
    assert hidden.is_active and not placeholder.is_active and not chem.is_active
