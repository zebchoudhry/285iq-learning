import json
import math
import random
import re
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from rest_framework.test import APIClient

from learning.generators.templates_science import REACTIONS, parse_formula
from learning.models import Flashcard, GameSession, Subject, Topic
from learning.services import games
from users.models import UserAchievement, UserProfile

SEEDS = range(300)


def rounds_for(slug, seed=0):
    return games.get_game(slug).make_rounds(random.Random(seed))


# ---------------------------------------------------------------------------
# Round builders
# ---------------------------------------------------------------------------
def test_prime_rounds_are_balanced_and_correct():
    for seed in SEEDS:
        rounds = rounds_for("prime-or-not", seed)
        numbers = [r["public"]["n"] for r in rounds]
        assert len(numbers) == 20 and len(set(numbers)) == 20
        assert sum(r["private"]["prime"] for r in rounds) == 10
        for r in rounds:
            n = r["public"]["n"]
            assert r["private"]["prime"] == (n > 1 and all(n % d for d in range(2, n)))


def test_balance_rounds_are_distinct_and_really_balanced():
    for seed in SEEDS:
        rounds = rounds_for("balance-it", seed)
        assert len(rounds) == 6 and len({tuple(r["public"]["left"] + r["public"]["right"]) for r in rounds}) == 6
        for r in rounds:
            p = r["private"]
            assert games._atom_totals(p["left"], p["coeffs"][:len(p["left"])]) == \
                games._atom_totals(p["right"], p["coeffs"][len(p["left"]):])


def test_compound_rounds_are_distinct_and_neutral():
    for seed in SEEDS:
        rounds = rounds_for("build-the-compound", seed)
        assert len({(r["public"]["cation"]["name"], r["public"]["anion"]["name"]) for r in rounds}) == 8
        for r in rounds:
            p, pub = r["private"], r["public"]
            assert p["n_c"] * pub["cation"]["charge"] == p["n_a"] * pub["anion"]["charge"]
            assert math.gcd(p["n_c"], p["n_a"]) == 1


def test_decay_rounds_reach_their_target():
    for seed in SEEDS:
        for r in rounds_for("decay-chain", seed):
            a, z = r["private"]["start"]["A"], r["private"]["start"]["Z"]
            for kind in r["private"]["example"]:
                a, z = games._decay_step(a, z, kind)
            assert (a, z) == (r["public"]["target"]["A"], r["public"]["target"]["Z"])
            assert any(k != "gamma" for k in r["private"]["example"])
            assert len(r["private"]["example"]) == r["public"]["steps"]


def correct_lines(title):
    """Recompute the correct worked solution for a Spot the Mistake title."""
    if m := re.fullmatch(r"Solve (\d+)x \+ (\d+) = (\d+)", title):
        a, b, c = map(int, m.groups())
        return [f"{a}x + {b} = {c}", f"{a}x = {c} − {b}", f"{a}x = {c - b}", f"x = {c - b} ÷ {a}", f"x = {(c - b) // a}"]
    if m := re.fullmatch(r"Expand and simplify (\d+)\(x \+ (\d+)\) \+ (\d+)x", title):
        p, q, r = map(int, m.groups())
        return [f"{p}(x + {q}) + {r}x", f"= {p}x + {p * q} + {r}x", f"= {p + r}x + {p * q}"]
    m = re.fullmatch(r"Work out (\d+)/(\d+) \+ (\d+)/(\d+)", title)
    a, b, c, d = map(int, m.groups())
    return [f"{a}/{b} + {c}/{d}", f"= {a * d}/{b * d} + {c * b}/{b * d}", f"= {a * d + c * b}/{b * d}"]


def test_spot_the_mistake_lines_are_right_until_the_one_wrong_line():
    seen_families = set()
    for seed in SEEDS:
        rounds = rounds_for("spot-the-mistake", seed)
        assert len({r["public"]["title"] for r in rounds}) == 6
        for r in rounds:
            lines, wrong = r["public"]["lines"], r["private"]["wrong"]
            correct = correct_lines(r["public"]["title"])
            assert 1 <= wrong < len(lines)
            assert lines[:wrong] == correct[:wrong], r
            assert lines[wrong] != correct[wrong], r
            assert r["private"]["why"]
            seen_families.add(r["public"]["title"].split()[0])
    assert seen_families == {"Solve", "Expand", "Work"}


@pytest.mark.django_db
def test_memory_rounds_need_enough_flashcards_in_one_topic():
    with pytest.raises(games.GameError):
        rounds_for("memory-match")
    subject = Subject.objects.create(name="biology", display_name="Biology")
    topic = Topic.objects.create(subject=subject, name="Cells", order=1)
    for i in range(5):
        Flashcard.objects.create(topic=topic, front=f"Term {i}", back=f"Definition {i}")
    with pytest.raises(games.GameError):
        rounds_for("memory-match")
    Flashcard.objects.create(topic=topic, front="Term 5", back="Definition 5")
    rounds = rounds_for("memory-match")
    tiles = rounds[0]["public"]["tiles"]
    assert len(rounds) == 6 and len(tiles) == 12
    for slot in range(6):
        pair = [t for t in tiles if t["pair"] == slot]
        assert {t["side"] for t in pair} == {"term", "definition"}
        term = next(t for t in pair if t["side"] == "term")["text"]
        definition = next(t for t in pair if t["side"] == "definition")["text"]
        assert definition == f"Definition {term.split()[1]}"


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------
def test_prime_grading():
    ok, detail = games._prime_grade({"n": 37, "prime": True}, True)
    assert ok and "prime" in detail
    ok, detail = games._prime_grade({"n": 51, "prime": False}, False)
    assert ok and "3 × 17" in detail
    for bad in (None, "true", 1, 0):
        assert not games._prime_grade({"n": 51, "prime": False}, bad)[0]
    assert not games._prime_grade({"n": 37, "prime": True}, False)[0]


def balance_private(index=0):
    left, right, coeffs = REACTIONS[index]
    return {"left": left, "right": right, "coeffs": coeffs}, coeffs


def test_balance_grading():
    private, coeffs = balance_private(5)  # CH4 + O2 -> CO2 + H2O
    assert games._balance_grade(private, coeffs)[0]
    ok, detail = games._balance_grade(private, [c * 2 for c in coeffs])
    assert not ok and "smallest" in detail
    assert not games._balance_grade(private, [1, 1, 1, 1])[0]
    for bad in (None, "2,1,2", [1], [True, 1, 1, 1], [0, 2, 1, 2], [1, 2, 1, 2.0], [1, 2, 1, 99]):
        assert not games._balance_grade(private, bad)[0]
    # any balanced answer in lowest terms is accepted, not only the stored one
    for left, right, stored in REACTIONS:
        p = {"left": left, "right": right, "coeffs": stored}
        assert games._balance_grade(p, list(stored))[0]


def test_compound_grading():
    private = {"n_c": 1, "n_a": 2, "formula": "Mg(OH)2", "cation": "magnesium", "anion": "hydroxide",
               "c_charge": 2, "a_charge": 1}
    ok, detail = games._compound_grade(private, [1, 2])
    assert ok and "Mg(OH)2" in detail
    for bad in ([2, 1], [2, 4], [1], None, [1, "2"], [True, 2]):
        assert not games._compound_grade(private, bad)[0]


def test_decay_grading_accepts_any_order_that_reaches_the_target():
    private = {"start": {"A": 238, "Z": 92}, "target": {"A": 230, "Z": 89}, "example": ["alpha", "alpha", "beta"]}
    for ok_answer in (["alpha", "alpha", "beta"], ["beta", "alpha", "alpha"], ["alpha", "beta", "alpha"]):
        assert games._decay_grade(private, ok_answer)[0]
    for bad in (["alpha", "beta", "beta"], ["gamma", "alpha", "beta"], ["alpha", "alpha"], None,
                ["alpha", "alpha", "neutron"], "alpha"):
        assert not games._decay_grade(private, bad)[0]


def test_spot_grading():
    private = {"wrong": 2, "why": "Because."}
    assert games._spot_grade(private, 2)[0]
    assert "Line 3" in games._spot_grade(private, 0)[1]
    for bad in (0, 1, 3, None, "2", True, 2.0):
        assert not games._spot_grade(private, bad)[0]


# ---------------------------------------------------------------------------
# Sessions, XP and limits
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    u = get_user_model().objects.create_user(username="player", password="x-test-pass")
    UserProfile.objects.create(student=u)
    return u


def age(session, seconds):
    GameSession.objects.filter(pk=session.pk).update(started_at=timezone.now() - timedelta(seconds=seconds))
    session.refresh_from_db()


def play_perfect_balance(session):
    for i, r in enumerate(session.rounds):
        assert games.submit_answer(session, i, r["private"]["coeffs"])["correct"]


def test_public_rounds_never_leak_answers(user):
    for slug in ("prime-or-not", "balance-it", "build-the-compound", "decay-chain", "spot-the-mistake"):
        session = games.start_session(user, slug, random.Random(1))
        blob = json.dumps(games.public_rounds(session))
        for secret in ('"private"', '"coeffs"', '"wrong"', '"why"', '"example"', '"prime"', '"formula"', '"n_c"'):
            assert secret not in blob, (slug, secret)


def test_perfect_game_pays_xp_and_levels_the_profile(user):
    session = games.start_session(user, "balance-it", random.Random(1))
    play_perfect_balance(session)
    age(session, 60)
    result = games.finish_session(session)
    assert (result["score"], result["total"], result["xp_earned"]) == (6, 6, 3 * 6 + 10)
    user.profile.refresh_from_db()
    assert user.profile.total_xp == 28
    assert result["rounds"][0]["detail"].startswith("Balanced")


def test_below_80_percent_gets_no_bonus(user):
    session = games.start_session(user, "balance-it", random.Random(1))
    for i, r in enumerate(session.rounds):
        games.submit_answer(session, i, r["private"]["coeffs"] if i < 4 else [1] * 4)
    age(session, 60)
    assert games.finish_session(session)["xp_earned"] == 3 * 4  # 4/6 correct


def test_finishing_faster_than_a_human_pays_nothing(user):
    session = games.start_session(user, "balance-it", random.Random(1))
    play_perfect_balance(session)
    result = games.finish_session(session)  # started a moment ago
    assert result["xp_earned"] == 0 and result["score"] == 6


def test_daily_cap(user):
    done = games.start_session(user, "balance-it", random.Random(2))
    GameSession.objects.filter(pk=done.pk).update(finished_at=timezone.now(), xp_awarded=140)
    session = games.start_session(user, "balance-it", random.Random(1))
    play_perfect_balance(session)
    age(session, 60)
    result = games.finish_session(session)
    assert result["xp_earned"] == 10 and result["xp_possible"] == 28 and result["daily_cap_reached"]
    assert games.game_xp_today(user) == 150


def test_answers_are_graded_once_and_rounds_are_checked(user):
    session = games.start_session(user, "spot-the-mistake", random.Random(1))
    wrong = session.rounds[0]["private"]["wrong"]
    first = games.submit_answer(session, 0, wrong)
    assert first["correct"] and not first["already_answered"]
    again = games.submit_answer(session, 0, wrong + 1)  # changing the answer afterwards changes nothing
    assert again["correct"] and again["already_answered"]
    for bad in (-1, 6, "0", None, True):
        with pytest.raises(games.GameError):
            games.submit_answer(session, bad, 0)


def test_finish_once_and_no_answers_after(user):
    session = games.start_session(user, "balance-it", random.Random(1))
    games.finish_session(session)
    with pytest.raises(games.GameError):
        games.finish_session(session)
    with pytest.raises(games.GameError):
        games.submit_answer(session, 0, [1, 1, 1])


def test_timed_game_rejects_late_answers_and_old_sessions_expire(user):
    session = games.start_session(user, "prime-or-not", random.Random(1))
    assert games.submit_answer(session, 0, True)
    age(session, 60 + games.TIMER_GRACE_S + 2)
    with pytest.raises(games.GameError, match="Time"):
        games.submit_answer(session, 1, True)
    old = games.start_session(user, "balance-it", random.Random(1))
    age(old, 3 * 3600)
    with pytest.raises(games.GameError, match="expired"):
        games.submit_answer(old, 0, [1, 1, 1])


def test_unanswered_rounds_count_as_wrong(user):
    session = games.start_session(user, "prime-or-not", random.Random(1))
    games.submit_answer(session, 0, session.rounds[0]["private"]["prime"])
    age(session, 30)
    result = games.finish_session(session)
    assert (result["score"], result["total"]) == (1, 20) and len(result["rounds"]) == 20


def test_achievements(user):
    session = games.start_session(user, "balance-it", random.Random(1))
    play_perfect_balance(session)
    age(session, 60)
    games.finish_session(session)
    slugs = set(UserAchievement.objects.filter(user_profile=user.profile).values_list("achievement__slug", flat=True))
    assert slugs == {"game_on", "perfect_round"}
    # a poor game does not repeat or add anything
    session2 = games.start_session(user, "balance-it", random.Random(2))
    games.finish_session(session2)
    assert UserAchievement.objects.filter(user_profile=user.profile).count() == 2


def test_hub_summary_reports_plays_and_best(user):
    games.finish_session(games.start_session(user, "balance-it", random.Random(1)))
    session = games.start_session(user, "balance-it", random.Random(2))
    play_perfect_balance(session)
    games.finish_session(session)
    summary = {g["slug"]: g for g in games.hub_summary(user)}
    assert summary["balance-it"]["plays"] == 2 and summary["balance-it"]["best_pct"] == 100
    assert summary["decay-chain"]["plays"] == 0 and len(summary) == 6


# ---------------------------------------------------------------------------
# API and pages
# ---------------------------------------------------------------------------
@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def test_api_full_game(client, user):
    assert len(client.get("/api/games/").data["games"]) == 6
    started = client.post("/api/games/balance-it/start/")
    assert started.status_code == 200 and len(started.data["rounds"]) == 6
    session = GameSession.objects.get(id=started.data["session_id"])
    for i, r in enumerate(session.rounds):
        res = client.post(f"/api/games/session/{session.id}/answer/", {"round": i, "answer": r["private"]["coeffs"]}, format="json")
        assert res.status_code == 200 and res.data["correct"]
    age(session, 60)
    done = client.post(f"/api/games/session/{session.id}/finish/")
    assert done.status_code == 200 and done.data["xp_earned"] == 28
    assert client.post(f"/api/games/session/{session.id}/finish/").status_code == 400
    assert client.get("/api/games/").data["xp_today"] == 28


def test_api_errors_and_ownership(client, user):
    assert client.post("/api/games/nope/start/").status_code == 400
    assert client.post("/api/games/memory-match/start/").status_code == 400  # no flashcards yet
    started = client.post("/api/games/decay-chain/start/")
    sid = started.data["session_id"]
    assert client.post(f"/api/games/session/{sid}/answer/", {"round": 99, "answer": []}, format="json").status_code == 400
    stranger = get_user_model().objects.create_user(username="stranger", password="x-test-pass")
    other = APIClient()
    other.force_authenticate(stranger)
    assert other.post(f"/api/games/session/{sid}/answer/", {"round": 0, "answer": []}, format="json").status_code == 404
    assert other.post(f"/api/games/session/{sid}/finish/").status_code == 404
    assert APIClient().get("/api/games/").status_code in (401, 403)


def test_pages(user):
    anon = Client()
    assert anon.get("/games/").status_code == 302 and anon.get("/games/prime-or-not/").status_code == 302
    c = Client()
    c.force_login(user)
    hub = c.get("/games/")
    assert hub.status_code == 200 and "csrftoken" in hub.cookies
    play = c.get("/games/prime-or-not/")
    assert play.status_code == 200 and b"Prime or Not" in play.content
    assert c.get("/games/not-a-game/").status_code == 404
