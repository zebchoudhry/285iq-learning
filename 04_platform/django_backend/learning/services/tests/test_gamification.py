from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from learning.models import BossBattle, Lesson, Question, QuizAttempt, Subject, Topic
from learning.services import boss_battle, gamification
from users.models import Achievement, UserAchievement, UserProfile


# ---------------------------------------------------------------------------
# Pure rules
# ---------------------------------------------------------------------------
def test_levels_get_harder_by_50_xp_each_time():
    assert [gamification.xp_to_reach(n) for n in (1, 2, 3, 4, 5)] == [0, 100, 250, 450, 700]
    assert gamification.level_for_xp(0)["level"] == 1
    assert gamification.level_for_xp(99)["level"] == 1
    assert gamification.level_for_xp(100)["level"] == 2
    assert gamification.level_for_xp(249)["level"] == 2
    assert gamification.level_for_xp(250)["level"] == 3


def test_level_progress_and_rank():
    info = gamification.level_for_xp(175)  # level 2 starts at 100 and needs 150 more
    assert (info["level"], info["xp_into_level"], info["xp_for_next_level"], info["progress_pct"]) == (2, 75, 150, 50)
    assert gamification.rank_for_level(1) == "Rookie"
    assert gamification.rank_for_level(3) == "Lifter"
    assert gamification.rank_for_level(10) == "Athlete"
    assert gamification.rank_for_level(40) == "Legend"


@pytest.mark.parametrize("combo,xp", [(0, 10), (1, 11), (3, 13), (10, 20), (25, 20)])
def test_combo_boosts_correct_answers_up_to_double(combo, xp):
    assert gamification.reward_for_attempt(True, combo, False)["xp"] == xp


def test_wrong_answers_earn_flat_xp_and_break_the_combo():
    reward = gamification.reward_for_attempt(False, 7, True)
    assert (reward["xp"], reward["combo"], reward["weak_spot_bonus_xp"]) == (2, 0, 0)


def test_weak_spot_bonus_adds_on_top_of_combo():
    reward = gamification.reward_for_attempt(True, 5, True)
    assert reward["xp"] == 15 + gamification.WEAK_SPOT_BONUS
    assert reward["weak_spot_fixed"] and reward["combo"] == 6


def test_reward_payload_falls_back_to_flat_xp():
    assert gamification.reward_payload(None, True) == {"xp_earned": 10}
    assert gamification.reward_payload(None, False) == {"xp_earned": 2}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def world(db):
    subject = Subject.objects.create(name="mathematics", display_name="GCSE Maths")
    topic = Topic.objects.create(subject=subject, name="Number", order=1)
    lesson = Lesson.objects.create(topic=topic, title="1.1 - Place Value", content="x", order=1)
    questions = [
        Question.objects.create(lesson=lesson, question_text=f"Question {i}?", correct_answer="ok",
                                explanation=f"Because {i}.")
        for i in range(20)
    ]
    user = get_user_model().objects.create_user(
        username="kid", password="x-test-pass", subscription_status="pro_monthly")
    UserProfile.objects.create(student=user)
    return {"subject": subject, "topic": topic, "lesson": lesson, "questions": questions, "user": user}


def attempt(user, question, correct, minutes_ago=0):
    a = QuizAttempt.objects.create(student=user, question=question, is_correct=correct)
    QuizAttempt.objects.filter(pk=a.pk).update(attempted_at=timezone.now() - timedelta(minutes=minutes_ago))
    return a


# ---------------------------------------------------------------------------
# Combo and weak spots from history
# ---------------------------------------------------------------------------
def test_combo_counts_recent_consecutive_correct_answers(world):
    user, qs = world["user"], world["questions"]
    attempt(user, qs[0], False, 9)
    for i, mins in enumerate((6, 4, 2)):
        attempt(user, qs[i + 1], True, mins)
    assert gamification.current_combo(user) == 3


def test_a_wrong_answer_resets_the_combo(world):
    user, qs = world["user"], world["questions"]
    attempt(user, qs[0], True, 6)
    attempt(user, qs[1], False, 4)
    attempt(user, qs[2], True, 2)
    assert gamification.current_combo(user) == 1


def test_a_long_gap_breaks_the_combo(world):
    user, qs = world["user"], world["questions"]
    attempt(user, qs[0], True, 120)
    attempt(user, qs[1], True, 119)
    assert gamification.current_combo(user) == 0
    attempt(user, qs[2], True, 5)
    assert gamification.current_combo(user) == 1


def test_weak_spot_needs_a_wrong_answer_over_an_hour_ago(world):
    user, q = world["user"], world["questions"][0]
    assert not gamification.is_weak_spot_fixed(user, q)
    attempt(user, q, False, 10)
    assert not gamification.is_weak_spot_fixed(user, q), "too recent: could be farmed"
    QuizAttempt.objects.all().delete()
    attempt(user, q, False, 180)
    assert gamification.is_weak_spot_fixed(user, q)
    attempt(user, q, True, 120)
    assert not gamification.is_weak_spot_fixed(user, q), "already fixed since"


def test_award_xp_levels_up_and_keeps_profile_in_step(world):
    user = world["user"]
    result = gamification.award_xp(user, 120)
    assert result["leveled_up"] and result["level"] == 2 and result["previous_level"] == 1
    user.profile.refresh_from_db()
    assert (user.profile.total_xp, user.profile.current_level) == (120, 2)
    assert not gamification.award_xp(user, 10)["leveled_up"]


def test_award_xp_without_a_profile_does_not_crash(db):
    user = get_user_model().objects.create_user(username="noprofile", password="x-test-pass")
    assert gamification.award_xp(user, 50)["leveled_up"] is False


# ---------------------------------------------------------------------------
# Attempts endpoint
# ---------------------------------------------------------------------------
@pytest.fixture
def client(world):
    c = APIClient()
    c.force_authenticate(world["user"])
    return c


def post_attempt(client, question, answer):
    return client.post("/api/attempts/", {"question_id": question.id, "answer": answer}, format="json")


def test_attempts_build_a_combo_and_report_it(world, client):
    qs = world["questions"]
    first = post_attempt(client, qs[0], "ok").data
    second = post_attempt(client, qs[1], "ok").data
    third = post_attempt(client, qs[2], "ok").data
    assert [first["xp_earned"], second["xp_earned"], third["xp_earned"]] == [10, 11, 12]
    assert (third["combo"], third["multiplier"]) == (3, 1.2)
    world["user"].profile.refresh_from_db()
    assert world["user"].profile.total_xp == 33
    wrong = post_attempt(client, qs[3], "nope").data
    assert wrong["xp_earned"] == 2 and wrong["combo"] == 0


def test_fixing_a_weak_spot_pays_a_bonus(world, client):
    user, q = world["user"], world["questions"][0]
    attempt(user, q, False, 180)
    data = post_attempt(client, q, "ok").data
    assert data["weak_spot_fixed"] and data["weak_spot_bonus_xp"] == 10 and data["xp_earned"] == 20


def test_level_up_is_reported(world, client):
    world["user"].profile.total_xp = 95
    world["user"].profile.save()
    data = post_attempt(client, world["questions"][0], "ok").data
    assert data["leveled_up"] and data["level"] == 2 and data["rank"] == "Rookie"


def test_profile_api_returns_level_and_rank(world, client):
    world["user"].profile.total_xp = 260
    world["user"].profile.save()
    me = client.get("/api/gamification/me/").data
    assert (me["level"], me["rank"], me["total_xp"]) == (3, "Lifter", 260)
    profile = client.get("/api/users/auth/current-user/").data.get("profile") or {}
    assert profile.get("current_level") == 3 and profile.get("rank") == "Lifter"


# ---------------------------------------------------------------------------
# Boss battles: rules
# ---------------------------------------------------------------------------
def test_battle_needs_enough_questions(db):
    subject = Subject.objects.create(name="biology", display_name="Biology")
    topic = Topic.objects.create(subject=subject, name="Tiny", order=1)
    lesson = Lesson.objects.create(topic=topic, title="1.1 - A", content="x", order=1)
    for i in range(3):
        Question.objects.create(lesson=lesson, question_text=f"q{i}", correct_answer="a")
    user = get_user_model().objects.create_user(username="u", password="x-test-pass")
    with pytest.raises(boss_battle.BossError):
        boss_battle.start_battle(user, topic)


def test_battle_mixes_in_weak_questions_and_resumes(world):
    user, topic, qs = world["user"], world["topic"], world["questions"]
    for q in qs[:3]:
        attempt(user, q, False, 200)
    battle = boss_battle.start_battle(user, topic)
    assert battle.max_rounds == 15 and len(set(battle.question_ids)) == 15
    assert set(battle.weak_question_ids) == {q.id for q in qs[:3]}
    assert set(battle.weak_question_ids) <= set(battle.question_ids)
    assert boss_battle.start_battle(user, topic).id == battle.id


def test_weak_questions_are_capped_at_five(world):
    for q in world["questions"][:9]:
        attempt(world["user"], q, False, 200)
    battle = boss_battle.start_battle(world["user"], world["topic"])
    assert len(battle.weak_question_ids) == 5


def make_battle(world, ids=None, weak=()):
    ids = ids or [q.id for q in world["questions"][:15]]
    return BossBattle.objects.create(
        student=world["user"], topic=world["topic"], boss_name="Number Titan",
        question_ids=ids, weak_question_ids=list(weak), max_rounds=len(ids))


def test_damage_grows_with_the_combo_and_caps(world):
    battle = make_battle(world)
    battle.max_hp = battle.hp = 500  # a tougher boss, so the cap is visible
    damage = []
    for qid in battle.question_ids[:8]:
        damage.append(boss_battle.apply_answer(battle, qid, True)["damage"])
    assert damage == [10, 12, 14, 16, 18, 20, 20, 20]


def test_critical_hit_on_weak_question(world):
    ids = [q.id for q in world["questions"][:15]]
    battle = make_battle(world, ids, weak=[ids[0]])
    result = boss_battle.apply_answer(battle, ids[0], True)
    assert result["critical"] and result["damage"] == 20


def test_wrong_answer_heals_resets_combo_and_cannot_overheal(world):
    battle = make_battle(world)
    ids = battle.question_ids
    boss_battle.apply_answer(battle, ids[0], False)
    assert battle.hp == battle.max_hp, "full health stays full"
    boss_battle.apply_answer(battle, ids[1], True)
    boss_battle.apply_answer(battle, ids[2], True)
    assert battle.combo == 2 and battle.hp == 100 - 10 - 12
    result = boss_battle.apply_answer(battle, ids[3], False)
    assert result["healed"] == 8 and battle.hp == 100 - 22 + 8 and battle.combo == 0


def test_beating_the_boss_awards_xp_and_an_achievement(world):
    battle = make_battle(world)
    for qid in battle.question_ids:
        result = boss_battle.apply_answer(battle, qid, True)
        if result["finished"]:
            break
    battle.refresh_from_db()
    assert battle.status == "won" and battle.hp == 0 and battle.xp_awarded == 50
    world["user"].profile.refresh_from_db()
    assert world["user"].profile.total_xp == 50
    assert UserAchievement.objects.filter(user_profile=world["user"].profile, achievement__slug="boss_slayer").exists()


def test_boss_escapes_when_questions_run_out(world):
    battle = make_battle(world)
    for qid in battle.question_ids:
        boss_battle.apply_answer(battle, qid, False)
    battle.refresh_from_db()
    assert battle.status == "escaped" and battle.xp_awarded == 0 and battle.finished_at


def test_cannot_answer_out_of_order_or_after_the_end(world):
    battle = make_battle(world)
    with pytest.raises(boss_battle.BossError):
        boss_battle.apply_answer(battle, battle.question_ids[5], True)
    for qid in battle.question_ids:
        boss_battle.apply_answer(battle, qid, False)
    with pytest.raises(boss_battle.BossError):
        boss_battle.apply_answer(battle, battle.question_ids[0], True)


def test_boss_hunter_after_five_different_topics(world):
    subject = world["subject"]
    for i in range(5):
        topic = Topic.objects.create(subject=subject, name=f"T{i}", order=10 + i)
        lesson = Lesson.objects.create(topic=topic, title=f"9.{i} - L", content="x", order=1)
        ids = [Question.objects.create(lesson=lesson, question_text=f"t{i}q{j}", correct_answer="ok").id for j in range(6)]
        battle = BossBattle.objects.create(student=world["user"], topic=topic, boss_name="B", question_ids=ids,
                                           max_rounds=6, hp=10)
        boss_battle.apply_answer(battle, ids[0], True)
    assert UserAchievement.objects.filter(user_profile=world["user"].profile, achievement__slug="boss_hunter").exists()


# ---------------------------------------------------------------------------
# Boss battles: API and page
# ---------------------------------------------------------------------------
def test_api_full_fight(world, client):
    started = client.post("/api/boss/start/", {"topic_id": world["topic"].id}, format="json")
    assert started.status_code == 200
    battle_id, question = started.data["battle"]["id"], started.data["question"]
    assert "correct_answer" not in question and started.data["battle"]["hp"] == 100

    for _ in range(15):
        r = client.post(f"/api/boss/{battle_id}/answer/", {"question_id": question["id"], "answer": "ok"}, format="json")
        assert r.status_code == 200
        question = r.data["question"]
        if question is None:
            break
    assert r.data["battle"]["status"] == "won"
    assert r.data["result"]["hit"]["finished"] and r.data["result"]["win_bonus_level"]
    assert QuizAttempt.objects.filter(student=world["user"]).count() == r.data["battle"]["answered"]


def test_api_wrong_answer_returns_feedback_and_heals(world, client):
    started = client.post("/api/boss/start/", {"topic_id": world["topic"].id}, format="json")
    battle_id, question = started.data["battle"]["id"], started.data["question"]
    client.post(f"/api/boss/{battle_id}/answer/", {"question_id": question["id"], "answer": "ok"}, format="json")
    q2 = client.get(f"/api/boss/{battle_id}/").data["question"]
    r = client.post(f"/api/boss/{battle_id}/answer/", {"question_id": q2["id"], "answer": "wrong"}, format="json")
    result = r.data["result"]
    assert result["is_correct"] is False and result["correct_answer"] == "ok" and result["explanation"]
    assert result["hit"]["healed"] == 8 and r.data["battle"]["hp"] == 90 + 8


def test_api_rejects_wrong_question_and_does_not_record_it(world, client):
    started = client.post("/api/boss/start/", {"topic_id": world["topic"].id}, format="json")
    battle = BossBattle.objects.get(id=started.data["battle"]["id"])
    other = next(q for q in world["questions"] if q.id != battle.question_ids[0])
    r = client.post(f"/api/boss/{battle.id}/answer/", {"question_id": other.id, "answer": "ok"}, format="json")
    assert r.status_code == 400
    assert QuizAttempt.objects.count() == 0


def test_api_other_students_battle_is_hidden(world, client):
    started = client.post("/api/boss/start/", {"topic_id": world["topic"].id}, format="json")
    stranger = get_user_model().objects.create_user(username="other", password="x-test-pass", subscription_status="pro_monthly")
    c2 = APIClient()
    c2.force_authenticate(stranger)
    assert c2.get(f"/api/boss/{started.data['battle']['id']}/").status_code == 404


def test_api_unknown_topic_and_logged_out(world, client):
    assert client.post("/api/boss/start/", {"topic_id": 999999}, format="json").status_code == 404
    assert APIClient().post("/api/boss/start/", {"topic_id": world["topic"].id}, format="json").status_code in (401, 403)


def test_free_tier_daily_limit_applies_in_battles(world):
    free = get_user_model().objects.create_user(username="freebie", password="x-test-pass")
    UserProfile.objects.create(student=free)
    c = APIClient()
    c.force_authenticate(free)
    started = c.post("/api/boss/start/", {"topic_id": world["topic"].id}, format="json")
    for q in world["questions"][:10]:
        attempt(free, q, True)
    r = c.post(f"/api/boss/{started.data['battle']['id']}/answer/",
               {"question_id": started.data["question"]["id"], "answer": "ok"}, format="json")
    assert r.status_code == 403


def test_boss_page_needs_login_and_shows_the_topic(world, client):
    anon = APIClient().get(f"/boss/{world['topic'].id}/")
    assert anon.status_code == 302
    from django.test import Client
    c = Client()
    c.force_login(world["user"])
    page = c.get(f"/boss/{world['topic'].id}/")
    assert page.status_code == 200 and b"Boss Battle: Number" in page.content
    assert "csrftoken" in page.cookies, "the page posts JSON, so it must set the CSRF cookie"
    assert c.get("/boss/999999/").status_code == 404
