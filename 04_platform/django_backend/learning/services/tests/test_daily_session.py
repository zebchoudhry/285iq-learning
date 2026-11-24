import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from learning.models import (
    Flashcard,
    Lesson,
    MistakeBankItem,
    MultipleChoiceOption,
    Question,
    QuizAttempt,
    StudentFlashcardProgress,
    Subject,
    Topic,
)
from learning.services.daily_session import build_daily_session
from users.models import StudentTopicPerformance

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def world():
    user = User.objects.create_user(username="kid", password="x-test-pass")
    subject = Subject.objects.create(name="biology", display_name="GCSE Biology")
    topic = Topic.objects.create(subject=subject, name="Cells", order=1)
    lesson = Lesson.objects.create(topic=topic, title="1.1 - Cells", content="x", order=1)
    questions = []
    for i in range(12):
        q = Question.objects.create(
            lesson=lesson, question_text=f"Cell question {i}?", correct_answer="Right",
            question_type="multiple_choice", explanation="Because.", difficulty_level=1 + i % 4,
        )
        for n, text in enumerate(["Right", "A", "B", "C"]):
            MultipleChoiceOption.objects.create(question=q, option_text=text, is_correct=n == 0, order=n)
        questions.append(q)
    return {"user": user, "subject": subject, "topic": topic, "lesson": lesson, "questions": questions}


def add_mistake(w, q, **kw):
    return MistakeBankItem.objects.create(student=w["user"], question=q, topic=w["topic"], **kw)


def add_due_card(w, front="Mitochondria?", due=None):
    card = Flashcard.objects.create(topic=w["topic"], front=front, back="Powerhouse")
    StudentFlashcardProgress.objects.create(
        student=w["user"], flashcard=card, due_date=due or timezone.now().date()
    )
    return card


def kinds(session):
    return [i["kind"] for i in session["items"]]


def test_brand_new_student_gets_a_session_from_an_untried_topic(world):
    s = build_daily_session(world["user"])
    assert s["count"] == 8 and s["focus_topic"] == "Cells"
    assert {i["source"] for i in s["items"]} == {"new_topic"}


def test_no_content_gives_empty_session(db):
    user = User.objects.create_user(username="lonely", password="x-test-pass")
    s = build_daily_session(user)
    assert s["count"] == 0 and s["items"] == [] and s["minutes"] == 0


def test_due_mistakes_come_first_and_are_capped(world):
    for q in world["questions"][:6]:
        add_mistake(world, q)
    s = build_daily_session(world["user"])
    mistakes = [i for i in s["items"] if i["source"] == "mistake"]
    assert len(mistakes) == 4
    assert s["items"][0]["source"] == "mistake"
    assert all(i["mistake_id"] for i in mistakes)


def test_mistakes_not_yet_due_or_finished_are_left_out(world):
    q = world["questions"]
    add_mistake(world, q[0], next_review_at=timezone.now() + timedelta(days=3))
    add_mistake(world, q[1], status="mastered")
    add_mistake(world, q[2], status="dismissed")
    s = build_daily_session(world["user"])
    assert not [i for i in s["items"] if i["source"] == "mistake"]


def test_due_flashcards_are_included_and_future_ones_are_not(world):
    add_due_card(world, "Due card")
    add_due_card(world, "Later card", due=timezone.now().date() + timedelta(days=2))
    s = build_daily_session(world["user"])
    cards = [i for i in s["items"] if i["kind"] == "flashcard"]
    assert [c["front"] for c in cards] == ["Due card"]


def test_flashcards_are_spread_through_the_session_not_blocked_at_the_end(world):
    for n in range(3):
        add_due_card(world, f"Card {n}")
    s = build_daily_session(world["user"])
    positions = [n for n, k in enumerate(kinds(s)) if k == "flashcard"]
    assert len(positions) == 3 and positions != [5, 6, 7]


def test_no_question_appears_twice(world):
    for q in world["questions"][:3]:
        add_mistake(world, q)
    ids = [i["question"]["id"] for i in build_daily_session(world["user"])["items"] if i["kind"] == "question"]
    assert len(ids) == len(set(ids))


def test_weakest_topic_is_chosen_and_labelled(world):
    other = Topic.objects.create(subject=world["subject"], name="Genetics", order=2)
    lesson2 = Lesson.objects.create(topic=other, title="2.1 - DNA", content="x", order=1)
    q = Question.objects.create(lesson=lesson2, question_text="DNA?", correct_answer="Right",
                                question_type="multiple_choice", explanation="x")
    for n, text in enumerate(["Right", "A", "B", "C"]):
        MultipleChoiceOption.objects.create(question=q, option_text=text, is_correct=n == 0, order=n)
    StudentTopicPerformance.objects.create(student=world["user"], topic=world["topic"], questions_attempted=10, questions_correct=9)
    StudentTopicPerformance.objects.create(student=world["user"], topic=other, questions_attempted=10, questions_correct=3)
    s = build_daily_session(world["user"])
    assert s["focus_topic"] == "Genetics"
    assert s["items"][0]["source"] == "weak_topic"


def test_difficulty_follows_gym_mode_struggling_students_get_easier_questions(world):
    user, topic = world["user"], world["topic"]
    for q in world["questions"][:6]:  # 6 attempts, 2 correct: weak, so guided practice (difficulty <= 2)
        QuizAttempt.objects.create(student=user, question=q, is_correct=q is world["questions"][0] or q is world["questions"][1])
    StudentTopicPerformance.objects.create(student=user, topic=topic, questions_attempted=6, questions_correct=2)
    s = build_daily_session(user)
    levels = [Question.objects.get(id=i["question"]["id"]).difficulty_level for i in s["items"] if i["kind"] == "question"]
    easy_available = Question.objects.filter(difficulty_level__lte=2).count()
    # every easy question is used before anything harder is topped up
    assert s["difficulty"] == "easier questions first"
    assert max(levels[:easy_available]) <= 2


def test_session_size_is_clamped(world):
    assert build_daily_session(world["user"], size=1)["count"] == 3
    assert build_daily_session(world["user"], size=99)["count"] <= 12  # 12 questions exist; cap is 15


def test_summary_and_minutes_describe_the_mix(world):
    add_mistake(world, world["questions"][0])
    add_due_card(world)
    s = build_daily_session(world["user"])
    assert "1 question you missed before" in s["summary"] and "1 flashcard due today" in s["summary"]
    assert s["minutes"] >= 1


def test_answers_are_never_leaked_in_the_payload(world):
    s = build_daily_session(world["user"])
    q = next(i for i in s["items"] if i["kind"] == "question")["question"]
    assert "correct_answer" not in q and all("is_correct" not in o for o in q["options"])


def test_other_students_data_does_not_leak(world):
    other = User.objects.create_user(username="other", password="x-test-pass")
    MistakeBankItem.objects.create(student=other, question=world["questions"][0], topic=world["topic"])
    s = build_daily_session(world["user"])
    assert not [i for i in s["items"] if i["source"] == "mistake"]


# ---- API and page ----------------------------------------------------------
def test_api_requires_login(db):
    assert Client().get("/api/today/").status_code in (401, 403)


def test_api_returns_session(world):
    c = Client()
    c.force_login(world["user"])
    r = c.get("/api/today/")
    assert r.status_code == 200 and r.json()["count"] == 8
    assert c.get("/api/today/?size=abc").status_code == 200


def test_page_redirects_anonymous_and_renders_for_students(world):
    assert Client().get("/today/")["Location"] == "/login/"
    c = Client()
    c.force_login(world["user"])
    r = c.get("/today/")
    assert r.status_code == 200 and b"Your 10 minutes" in r.content


def test_answering_through_the_session_uses_normal_attempt_endpoint_and_xp(world):
    c = Client()
    c.force_login(world["user"])
    item = next(i for i in c.get("/api/today/").json()["items"] if i["kind"] == "question")
    right = MultipleChoiceOption.objects.get(question_id=item["question"]["id"], is_correct=True)
    r = c.post("/api/attempts/", {"question_id": item["question"]["id"], "selected_option_id": right.id},
               content_type="application/json")
    assert r.status_code == 200 and r.json()["is_correct"] is True


def test_flashcard_rating_reschedules_a_session_card(world):
    card = add_due_card(world)
    c = Client()
    c.force_login(world["user"])
    r = c.post("/api/flashcards/review/", {"flashcard_id": card.id, "rating": "good"}, content_type="application/json")
    assert r.status_code == 200
    assert build_daily_session(world["user"])["count"] and not [
        i for i in build_daily_session(world["user"])["items"] if i["kind"] == "flashcard"
    ]
