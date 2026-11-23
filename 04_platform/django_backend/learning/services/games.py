"""
Learning mini-games.

Each game is a short run of rounds. The server builds the rounds with fresh numbers (using the
question-template data), keeps the answers private, grades every answer as it arrives so the
student gets instant feedback, and awards XP when the game is finished.

XP: 3 per correct round, +10 for 80% or better, capped at 150 game XP a day so the games can't
be ground for levels. Finishing faster than a human could play pays nothing.
"""
import math
import random
from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Tuple

from django.db.models import Sum
from django.utils import timezone

from learning.generators.engine import is_prime, tdec
from learning.generators.templates_science import (
    ALPHA_EMITTERS, ANIONS, BETA_EMITTERS, CATIONS, REACTIONS, _equation_text,
    ionic_formula, parse_formula,
)
from learning.models import Flashcard, GameSession
from learning.services import gamification

XP_PER_CORRECT = 3
COMPLETION_BONUS_XP = 10
BONUS_THRESHOLD = 0.8
DAILY_GAME_XP_CAP = 150
TIMER_GRACE_S = 5
MAX_SESSION_AGE = timedelta(hours=2)


class GameError(Exception):
    """A request that cannot be carried out; the message is safe to show."""


Round = Dict[str, dict]  # {"public": {...}, "private": {...}}


@dataclass(frozen=True)
class Game:
    slug: str
    title: str
    blurb: str
    area: str
    icon: str
    make_rounds: Callable[[random.Random], List[Round]]
    grade: Callable[[dict, object], Tuple[bool, str]]
    time_limit_s: Optional[int] = None
    min_seconds: int = 5  # a finish faster than this pays no XP


# ===========================================================================
# Prime or Not  (maths: primes and composites)
# ===========================================================================
def _prime_rounds(rng):
    primes = [n for n in range(2, 100) if is_prime(n)]
    tricky = [n for n in range(21, 100, 2) if not is_prime(n) and any(n % p == 0 for p in (3, 7))]
    other = [n for n in range(4, 100) if not is_prime(n) and n not in tricky]
    numbers = rng.sample(primes, 10) + rng.sample(tricky, 6) + rng.sample(other, 4)
    rng.shuffle(numbers)
    return [{"public": {"n": n}, "private": {"n": n, "prime": is_prime(n)}} for n in numbers]


def _prime_grade(private, answer):
    n = private["n"]
    if private["prime"]:
        detail = f"{n} is prime: its only factors are 1 and {n}."
    else:
        f = next(d for d in range(2, n + 1) if n % d == 0)
        detail = f"{n} is not prime: {n} = {f} × {n // f}."
    return (answer is True or answer is False) and answer == private["prime"], detail


# ===========================================================================
# Balance It  (chemistry: balancing equations)
# ===========================================================================
def _balance_rounds(rng):
    picks = rng.sample(REACTIONS, 6)
    return [
        {"public": {"left": left, "right": right},
         "private": {"left": left, "right": right, "coeffs": coeffs}}
        for left, right, coeffs in picks
    ]


def _atom_totals(species, coefficients):
    totals: Dict[str, int] = {}
    for s, c in zip(species, coefficients):
        for el, n in parse_formula(s).items():
            totals[el] = totals.get(el, 0) + n * c
    return totals


def _balance_grade(private, answer):
    left, right, coeffs = private["left"], private["right"], private["coeffs"]
    shown = _equation_text(left, right, coeffs)
    if not isinstance(answer, list) or len(answer) != len(left) + len(right):
        return False, f"The balanced equation is {shown}."
    if not all(isinstance(c, int) and not isinstance(c, bool) and 1 <= c <= 20 for c in answer):
        return False, f"The balanced equation is {shown}."
    balanced = _atom_totals(left, answer[:len(left)]) == _atom_totals(right, answer[len(left):])
    lowest = math.gcd(*answer) == 1
    if balanced and lowest:
        return True, f"Balanced: {shown}."
    if balanced:
        return False, f"That balances, but use the smallest whole numbers: {shown}."
    return False, f"The atoms don't match on both sides. The balanced equation is {shown}."


# ===========================================================================
# Build the Compound  (chemistry: ionic formulae)
# ===========================================================================
def _ion(ion):
    name, symbol, charge, poly = ion
    return {"name": name, "symbol": symbol, "charge": charge, "poly": poly}


def _compound_rounds(rng):
    pairs = set()
    while len(pairs) < 8:
        pairs.add((rng.randrange(len(CATIONS)), rng.randrange(len(ANIONS))))
    out = []
    for ci, ai in sorted(pairs, key=lambda _: rng.random()):
        cation, anion = CATIONS[ci], ANIONS[ai]
        lcm = math.lcm(cation[2], anion[2])
        out.append({
            "public": {"cation": _ion(cation), "anion": _ion(anion)},
            "private": {"n_c": lcm // cation[2], "n_a": lcm // anion[2],
                        "formula": ionic_formula(cation, anion),
                        "cation": cation[0], "anion": anion[0],
                        "c_charge": cation[2], "a_charge": anion[2]},
        })
    return out


def _compound_grade(private, answer):
    detail = (f"{private['cation'].capitalize()} {private['c_charge']}+ and {private['anion']} "
              f"{private['a_charge']}−: {private['n_c']} × {private['c_charge']} = "
              f"{private['n_a']} × {private['a_charge']}, so the formula is {private['formula']}.")
    ok = (isinstance(answer, list) and len(answer) == 2
          and all(isinstance(v, int) and not isinstance(v, bool) for v in answer)
          and answer == [private["n_c"], private["n_a"]])
    return ok, detail


# ===========================================================================
# Decay Chain  (physics: alpha, beta and gamma decay)
# ===========================================================================
DECAY_CHOICES = ("alpha", "beta", "gamma")


def _decay_step(a, z, kind):
    return {"alpha": (a - 4, z - 2), "beta": (a, z + 1), "gamma": (a, z)}[kind]


def _decay_rounds(rng):
    out = []
    for i in range(6):
        steps = 2 if i < 3 else 3
        name, z, a = rng.choice(ALPHA_EMITTERS + BETA_EMITTERS)
        while True:
            seq = [rng.choice(["alpha", "alpha", "beta", "beta", "gamma"]) for _ in range(steps)]
            if any(k != "gamma" for k in seq):
                break
        ta, tz = a, z
        for kind in seq:
            ta, tz = _decay_step(ta, tz, kind)
        out.append({
            "public": {"name": name, "start": {"A": a, "Z": z}, "steps": steps, "target": {"A": ta, "Z": tz}},
            "private": {"start": {"A": a, "Z": z}, "target": {"A": ta, "Z": tz}, "example": seq},
        })
    return out


def _decay_grade(private, answer):
    start, target, example = private["start"], private["target"], private["example"]
    ok_shape = (isinstance(answer, list) and len(answer) == len(example)
                and all(k in DECAY_CHOICES for k in answer))
    if ok_shape:
        a, z = start["A"], start["Z"]
        for kind in answer:
            a, z = _decay_step(a, z, kind)
        if (a, z) == (target["A"], target["Z"]):
            return True, f"Yes: {' then '.join(answer)} takes it to mass number {a}, atomic number {z}."
    return False, (f"One way is {' then '.join(example)}. Alpha: mass −4, atomic −2. "
                   f"Beta: atomic +1. Gamma: no change.")


# ===========================================================================
# Spot the Mistake  (maths: find the wrong line in a worked solution)
# ===========================================================================
def _spot_linear(rng):
    error = rng.choice(["sign", "slip", "divide"])
    a = rng.randint(2, 9) if error == "divide" else rng.choice([2, 4, 5])
    x, b = rng.randint(2, 12), rng.randint(2, 20)
    c = a * x + b
    diff = c - b
    lines = [f"{a}x + {b} = {c}", f"{a}x = {c} − {b}", f"{a}x = {diff}",
             f"x = {diff} ÷ {a}", f"x = {x}"]
    if error == "sign":
        lines[1:] = [f"{a}x = {c} + {b}", f"{a}x = {c + b}", f"x = {c + b} ÷ {a}", f"x = {tdec(Fraction(c + b, a))}"]
        wrong, why = 1, f"To get rid of + {b}, subtract {b} from both sides. It should be {a}x = {c} − {b}."
    elif error == "slip":
        d = rng.choice([1, -1, 10, -10])
        lines[2:] = [f"{a}x = {diff + d}", f"x = {diff + d} ÷ {a}", f"x = {tdec(Fraction(diff + d, a))}"]
        wrong, why = 2, f"{c} − {b} = {diff}, not {diff + d}."
    else:
        lines[3:] = [f"x = {diff} × {a}", f"x = {diff * a}"]
        wrong, why = 3, f"The {a} is multiplying x, so divide both sides by {a}, not multiply."
    return {"public": {"title": f"Solve {a}x + {b} = {c}", "lines": lines}, "private": {"wrong": wrong, "why": why}}


def _spot_expand(rng):
    while True:
        p, q, r = rng.randint(2, 6), rng.randint(2, 9), rng.randint(2, 5)
        if p * q != p + q and p * r != p + r:  # with 2 and 2 the "mistake" gives the right answer
            break
    error = rng.choice(["forgot", "add", "collect"])
    lines = [f"{p}(x + {q}) + {r}x", f"= {p}x + {p * q} + {r}x", f"= {p + r}x + {p * q}"]
    if error == "forgot":
        lines[1:] = [f"= {p}x + {q} + {r}x", f"= {p + r}x + {q}"]
        wrong, why = 1, f"The {p} multiplies everything in the bracket, so {p} × {q} = {p * q}, not {q}."
    elif error == "add":
        lines[1:] = [f"= {p}x + {p + q} + {r}x", f"= {p + r}x + {p + q}"]
        wrong, why = 1, f"Expanding multiplies: {p} × {q} = {p * q}, not {p} + {q}."
    else:
        lines[2] = f"= {p * r}x + {p * q}"
        wrong, why = 2, f"Collect like terms by adding: {p}x + {r}x = {p + r}x, not {p * r}x."
    return {"public": {"title": f"Expand and simplify {p}(x + {q}) + {r}x", "lines": lines},
            "private": {"wrong": wrong, "why": why}}


def _spot_fractions(rng):
    b, d = rng.sample(range(2, 8), 2)
    a = rng.choice([n for n in range(1, b) if math.gcd(n, b) == 1])  # fractions in simplest form
    c = rng.choice([n for n in range(1, d) if math.gcd(n, d) == 1])
    error = rng.choice(["tops_bottoms", "no_scale", "slip"])
    lines = [f"{a}/{b} + {c}/{d}", f"= {a * d}/{b * d} + {c * b}/{b * d}", f"= {a * d + c * b}/{b * d}"]
    if error == "tops_bottoms":
        lines[1:] = [f"= ({a} + {c})/({b} + {d})", f"= {a + c}/{b + d}"]
        wrong, why = 1, "You can't add the denominators. Write both fractions over a common denominator first."
    elif error == "no_scale":
        lines[1:] = [f"= {a}/{b * d} + {c}/{b * d}", f"= {a + c}/{b * d}"]
        wrong, why = 1, f"If the denominators become {b * d}, the numerators must be multiplied as well."
    else:
        lines[2] = f"= {a * d + c * b + 1}/{b * d}"
        wrong, why = 2, f"{a * d} + {c * b} = {a * d + c * b}, so the numerator is {a * d + c * b}."
    return {"public": {"title": f"Work out {a}/{b} + {c}/{d}", "lines": lines},
            "private": {"wrong": wrong, "why": why}}


def _spot_rounds(rng):
    makers = [_spot_linear, _spot_expand, _spot_fractions]
    out, titles = [], set()
    while len(out) < 6:
        r = rng.choice(makers)(rng)
        if r["public"]["title"] not in titles:
            titles.add(r["public"]["title"])
            out.append(r)
    return out


def _spot_grade(private, answer):
    ok = isinstance(answer, int) and not isinstance(answer, bool) and answer == private["wrong"]
    return ok, f"Line {private['wrong'] + 1} is wrong. {private['why']}"


# ===========================================================================
# Memory Match  (flashcards: match terms to definitions)
# ===========================================================================
PAIRS = 6


def _memory_rounds(rng):
    cards = [c for c in Flashcard.objects.filter(is_active=True).values("id", "topic_id", "front", "back")
             if 2 <= len(c["front"]) <= 60 and 2 <= len(c["back"]) <= 70]
    by_topic: Dict[int, list] = {}
    for c in cards:
        by_topic.setdefault(c["topic_id"], []).append(c)
    topics = [t for t, v in by_topic.items() if len(v) >= PAIRS]
    if not topics:
        raise GameError("There aren't enough flashcards for Memory Match yet.")
    chosen = rng.sample(by_topic[rng.choice(topics)], PAIRS)
    tiles = []
    for slot, c in enumerate(chosen):
        tiles.append({"pair": slot, "text": c["front"], "side": "term"})
        tiles.append({"pair": slot, "text": c["back"], "side": "definition"})
    rng.shuffle(tiles)
    shared = {"tiles": [{"id": i, **t} for i, t in enumerate(tiles)]}
    return [{"public": {"slot": s, **(shared if s == 0 else {})}, "private": {}} for s in range(PAIRS)]


def _memory_grade(private, answer):
    return answer is True, "Matched."


# ===========================================================================
# Registry
# ===========================================================================
GAMES: List[Game] = [
    Game("prime-or-not", "Prime or Not", "Sort 20 numbers into prime and composite against the clock.",
         "Maths · Number", "🔢", _prime_rounds, _prime_grade, time_limit_s=60, min_seconds=15),
    Game("balance-it", "Balance It", "Balance six chemical equations using the smallest whole numbers.",
         "Chemistry · Equations", "⚗️", _balance_rounds, _balance_grade),
    Game("build-the-compound", "Build the Compound", "Combine ions in the right numbers so the charges cancel.",
         "Chemistry · Ionic compounds", "🧪", _compound_rounds, _compound_grade),
    Game("decay-chain", "Decay Chain", "Choose alpha, beta or gamma steps to reach the target nucleus.",
         "Physics · Radioactive decay", "☢️", _decay_rounds, _decay_grade),
    Game("spot-the-mistake", "Spot the Mistake", "Find the line where a worked solution goes wrong.",
         "Maths · Algebra and fractions", "🕵️", _spot_rounds, _spot_grade),
    Game("memory-match", "Memory Match", "Match each key term to its definition in as few moves as you can.",
         "Flashcards", "🃏", _memory_rounds, _memory_grade, min_seconds=15),
]
BY_SLUG = {g.slug: g for g in GAMES}


# ===========================================================================
# Sessions
# ===========================================================================
def get_game(slug: str) -> Game:
    game = BY_SLUG.get(slug)
    if not game:
        raise GameError("Unknown game.")
    return game


def start_session(student, slug: str, rng: Optional[random.Random] = None) -> GameSession:
    game = get_game(slug)
    rounds = game.make_rounds(rng or random.Random())
    return GameSession.objects.create(student=student, slug=slug, rounds=rounds, total=len(rounds))


def public_rounds(session: GameSession) -> list:
    return [r["public"] for r in session.rounds]


def _check_open(session: GameSession):
    if session.finished_at:
        raise GameError("This game is already finished.")
    if timezone.now() - session.started_at > MAX_SESSION_AGE:
        raise GameError("This game has expired. Start a new one.")


def submit_answer(session: GameSession, index, answer) -> dict:
    """Grade one round. Answering the same round again returns the first result."""
    _check_open(session)
    game = get_game(session.slug)
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(session.rounds):
        raise GameError("That round doesn't exist.")
    if game.time_limit_s:
        elapsed = (timezone.now() - session.started_at).total_seconds()
        if elapsed > game.time_limit_s + TIMER_GRACE_S:
            raise GameError("Time's up.")
    key = str(index)
    if key in session.results:
        r = session.results[key]
        return {"correct": r["correct"], "detail": r["detail"], "already_answered": True}
    correct, detail = game.grade(session.rounds[index]["private"], answer)
    session.results[key] = {"answer": answer, "correct": bool(correct), "detail": detail}
    session.save(update_fields=["results"])
    return {"correct": bool(correct), "detail": detail, "already_answered": False}


def game_xp_today(student) -> int:
    today = timezone.localdate()
    return GameSession.objects.filter(student=student, finished_at__date=today).aggregate(
        total=Sum("xp_awarded"))["total"] or 0


def finish_session(session: GameSession) -> dict:
    _check_open(session)
    game = get_game(session.slug)
    now = timezone.now()
    score = sum(1 for r in session.results.values() if r["correct"])
    total = len(session.rounds)
    raw = XP_PER_CORRECT * score + (COMPLETION_BONUS_XP if total and score / total >= BONUS_THRESHOLD else 0)
    if (now - session.started_at).total_seconds() < game.min_seconds:
        raw = 0
    remaining = max(DAILY_GAME_XP_CAP - game_xp_today(session.student), 0)
    xp = min(raw, remaining)

    session.score, session.total, session.xp_awarded, session.finished_at = score, total, xp, now
    session.save(update_fields=["score", "total", "xp_awarded", "finished_at"])

    level = gamification.award_xp(session.student, xp) if xp else gamification.level_for_xp(
        getattr(getattr(session.student, "profile", None), "total_xp", 0))
    _award_game_achievements(session)
    return {
        "score": score, "total": total, "xp_earned": xp, "xp_possible": raw,
        "daily_cap_reached": raw > xp,
        "level": level.get("level"), "rank": level.get("rank"),
        "level_progress_pct": level.get("progress_pct"), "leveled_up": level.get("leveled_up", False),
        "rounds": [
            {"correct": session.results.get(str(i), {}).get("correct", False),
             "detail": session.results.get(str(i), {}).get("detail", "")}
            for i in range(total)
        ],
    }


def _award_game_achievements(session: GameSession):
    from users.achievements import award_achievement

    award_achievement(session.student, "game_on", "Game On", "Finish your first learning game.", "🎮")
    if session.total >= PAIRS and session.score == session.total:
        award_achievement(session.student, "perfect_round", "Perfect Round",
                          "Get every round right in a learning game.", "💯")


def hub_summary(student) -> list:
    """Every game with the student's plays and best score."""
    stats: Dict[str, dict] = {}
    for slug, score, total in GameSession.objects.filter(
        student=student, finished_at__isnull=False
    ).values_list("slug", "score", "total"):
        s = stats.setdefault(slug, {"plays": 0, "best_pct": 0})
        s["plays"] += 1
        if total:
            s["best_pct"] = max(s["best_pct"], round(100 * score / total))
    return [
        {"slug": g.slug, "title": g.title, "blurb": g.blurb, "area": g.area, "icon": g.icon,
         "time_limit_s": g.time_limit_s, **stats.get(g.slug, {"plays": 0, "best_pct": 0})}
        for g in GAMES
    ]
