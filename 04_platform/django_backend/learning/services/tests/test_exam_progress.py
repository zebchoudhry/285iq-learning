import pytest
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from learning.models import (
    Lesson,
    MultipleChoiceOption,
    Question,
    QuizAttempt,
    ReadinessSnapshot,
    StudentExamSettings,
    Subject,
    Topic,
)
from learning.services.daily_session import _allocate, build_daily_session, plan_topics
from learning.services.exam_progress import READY_TARGET, build_exam_progress
from learning.services.topic_mastery import topic_mastery

pytestmark = pytest.mark.django_db
User = get_user_model()


def make_topic(subject, name, order, nq=10):
    topic = Topic.objects.create(subject=subject, name=name, order=order)
    lesson = Lesson.objects.create(topic=topic, title=f"{order}.1 - {name}", content="x", order=1)
    qs = []
    for i in range(nq):
        q = Question.objects.create(lesson=lesson, question_text=f"{name} q{i}?", correct_answer="Right",
                                    question_type="multiple_choice", explanation="Because.", difficulty_level=1 + i % 3)
        for n, t in enumerate(["Right", "A", "B", "C"]):
            MultipleChoiceOption.objects.create(question=q, option_text=t, is_correct=n == 0, order=n)
        qs.append(q)
    return topic, qs


def answer(user, questions, results):
    for q, ok in zip(questions, results):
        QuizAttempt.objects.create(student=user, question=q, is_correct=ok)


@pytest.fixture
def world():
    user = User.objects.create_user(username="kid", password="x-test-pass")
    subject = Subject.objects.create(name="biology", display_name="GCSE Biology")
    weak, weak_qs = make_topic(subject, "Genetics", 1)
    mid, mid_qs = make_topic(subject, "Cells", 2)
    strong, strong_qs = make_topic(subject, "Organs", 3)
    return dict(user=user, subject=subject, weak=weak, mid=mid, strong=strong,
                weak_qs=weak_qs, mid_qs=mid_qs, strong_qs=strong_qs)


# ---- topic mastery --------------------------------------------------------
def test_mastery_untried_is_none(world):
    m = topic_mastery(world["user"], [world["weak"].id])
    assert m[world["weak"].id]["accuracy"] is None


def test_mastery_uses_only_recent_answers_so_it_recovers(world):
    u, qs = world["user"], world["weak_qs"]
    answer(u, qs[:10], [False] * 10)           # early struggle
    answer(u, qs[:10], [True] * 10)            # then improvement (newer rows)
    m = topic_mastery(u, [world["weak"].id])[world["weak"].id]
    assert m["accuracy"] == 1.0 and m["graduated"] is True


def test_graduation_needs_enough_answers_and_a_strong_recent_half(world):
    u, qs = world["user"], world["weak_qs"]
    answer(u, qs[:5], [True] * 5)
    assert topic_mastery(u, [world["weak"].id])[world["weak"].id]["graduated"] is False  # too few answers


# ---- planner ---------------------------------------------------------------
def test_weak_topic_gets_the_biggest_share(world):
    u = world["user"]
    answer(u, world["weak_qs"], [False] * 8 + [True] * 2)   # 20%
    answer(u, world["mid_qs"], [True] * 7 + [False] * 3)    # 70%
    answer(u, world["strong_qs"], [True] * 10)              # 100%, graduated
    session = build_daily_session(u)
    shares = {f["topic"]: f["questions"] for f in session["focus_topics"]}
    assert session["focus_topic"] == "Genetics"
    assert shares["Genetics"] > shares["Cells"] >= shares.get("Organs", 0)


def test_plan_shifts_away_from_a_topic_once_it_is_learned(world):
    u = world["user"]
    answer(u, world["weak_qs"], [False] * 10)
    answer(u, world["mid_qs"], [True] * 6 + [False] * 4)
    answer(u, world["strong_qs"], [True] * 10)  # Organs already learned, so only Cells and Genetics compete
    assert plan_topics(u)[0]["topic"] == world["weak"]
    answer(u, world["weak_qs"], [True] * 10)  # newer answers: now strong
    plan = plan_topics(u)
    assert plan[0]["topic"] == world["mid"]
    assert next(p for p in plan if p["topic"] == world["weak"])["source"] == "maintenance"


def test_graduated_topics_still_get_a_light_refresher(world):
    u = world["user"]
    for t in ("weak_qs", "mid_qs", "strong_qs"):
        answer(u, world[t], [True] * 10)
    reasons = {f["reason"] for f in build_daily_session(u)["focus_topics"]}
    assert reasons == {"maintenance"}


def test_nearer_exam_raises_subject_priority(world):
    other = Subject.objects.create(name="chemistry", display_name="GCSE Chemistry")
    ct, cqs = make_topic(other, "Bonding", 1)
    u = world["user"]
    answer(u, world["weak_qs"], [True] * 5 + [False] * 5)
    answer(u, cqs, [True] * 5 + [False] * 5)   # identical accuracy
    today = timezone.now().date()
    StudentExamSettings.objects.create(student=u, subject=world["subject"], exam_date=today + timedelta(days=170))
    StudentExamSettings.objects.create(student=u, subject=other, exam_date=today + timedelta(days=20))
    assert plan_topics(u)[0]["topic"] == ct


def test_students_with_exam_dates_only_practise_those_subjects(world):
    other = Subject.objects.create(name="physics", display_name="GCSE Physics")
    make_topic(other, "Forces", 1)
    u = world["user"]
    StudentExamSettings.objects.create(student=u, subject=world["subject"], exam_date=timezone.now().date() + timedelta(days=90))
    assert {p["topic"].subject_id for p in plan_topics(u)} == {world["subject"].id}


def test_allocate_sums_to_total_and_favours_weight(world):
    plan = [{"weight": 0.9}, {"weight": 0.3}, {"weight": 0.05}]
    for total in (3, 5, 8, 12):
        shares = _allocate(plan, total)
        assert sum(shares) == total and shares[0] >= shares[1] >= shares[2] >= 1
    assert _allocate([], 5) == [] and _allocate(plan, 0) == [0, 0, 0]


def test_session_still_fills_when_the_weak_topic_has_few_questions(world):
    u = world["user"]
    tiny, tqs = make_topic(world["subject"], "Tiny", 4, nq=2)
    answer(u, tqs, [False, False, False][:2])
    QuizAttempt.objects.create(student=u, question=tqs[0], is_correct=False)
    s = build_daily_session(u)
    ids = [i["question"]["id"] for i in s["items"] if i["kind"] == "question"]
    assert s["count"] == 8 and len(ids) == len(set(ids))


# ---- exam progress ----------------------------------------------------------
def settings_for(world, days=120, grade=7):
    return StudentExamSettings.objects.create(
        student=world["user"], subject=world["subject"],
        exam_date=timezone.now().date() + timedelta(days=days), target_grade=grade)


def test_no_exam_dates_reports_so(world):
    p = build_exam_progress(world["user"])
    assert p["has_exam_dates"] is False and p["subjects"] == [] and p["next_exam"] is None


def test_progress_fields_and_month_label(world):
    settings_for(world, days=120)
    s = build_exam_progress(world["user"])["subjects"][0]
    assert s["target"] == READY_TARGET and 0 <= s["score"] <= 100
    assert s["days_left"] == 120 and s["exam_month"]
    assert s["state"] in ("on_track", "behind") and s["rate_is_measured"] is False


def test_brand_new_student_far_from_exam_is_behind_with_a_session_target(world):
    settings_for(world, days=30)
    s = build_exam_progress(world["user"])["subjects"][0]
    assert s["state"] == "behind" and 1 <= s["sessions_per_week_needed"] <= 7


def test_exam_in_the_past(world):
    settings_for(world, days=-5)
    s = build_exam_progress(world["user"])["subjects"][0]
    assert s["state"] == "exam_passed" and s["sessions_per_week_needed"] is None


def test_snapshot_is_written_once_per_day_and_updates(world):
    settings_for(world)
    build_exam_progress(world["user"])
    build_exam_progress(world["user"])
    assert ReadinessSnapshot.objects.filter(student=world["user"]).count() == 1
    snap = ReadinessSnapshot.objects.get(student=world["user"])
    assert str(world["weak"].id) in snap.topic_mastery


def test_measured_rate_is_used_when_there_is_history(world):
    settings_for(world, days=60)
    today = timezone.now().date()
    u, subj = world["user"], world["subject"]
    ReadinessSnapshot.objects.create(student=u, subject=subj, taken_on=today - timedelta(days=21), score=10)
    ReadinessSnapshot.objects.create(student=u, subject=subj, taken_on=today - timedelta(days=7), score=40)
    s = build_exam_progress(u)["subjects"][0]
    assert s["rate_is_measured"] is True and s["history"][0]["score"] == 10


def test_next_exam_is_the_nearest_future_one(world):
    other = Subject.objects.create(name="physics", display_name="GCSE Physics")
    u = world["user"]
    today = timezone.now().date()
    StudentExamSettings.objects.create(student=u, subject=world["subject"], exam_date=today + timedelta(days=90))
    StudentExamSettings.objects.create(student=u, subject=other, exam_date=today + timedelta(days=30))
    StudentExamSettings.objects.create(
        student=u, subject=Subject.objects.create(name="maths", display_name="GCSE Maths"), exam_date=today - timedelta(days=3))
    assert build_exam_progress(u)["next_exam"]["subject"] == "GCSE Physics"


def test_api_requires_login_and_returns_json(world):
    assert Client().get("/api/exam-progress/").status_code in (401, 403)
    settings_for(world)
    c = Client()
    c.force_login(world["user"])
    r = c.get("/api/exam-progress/")
    assert r.status_code == 200 and r.json()["has_exam_dates"] is True


def test_onboarding_page_offers_month_only_entry(world):
    c = Client()
    c.force_login(world["user"])
    assert b'type="month"' in c.get("/onboarding/exam-dates/").content
