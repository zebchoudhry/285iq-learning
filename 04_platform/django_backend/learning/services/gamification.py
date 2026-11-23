"""
XP, levels and combos.

XP rewards effort and fixing weak spots, not volume:
  - a correct answer is worth 10 XP, boosted by a combo of consecutive correct
    answers (+10% per answer, up to x2 at 10 in a row)
  - a correct answer to a question the student last got wrong (at least an hour
    earlier, so it can't be farmed by getting it wrong on purpose) earns a
    weak-spot bonus of 10 XP
  - a wrong answer earns 2 XP for trying, never boosted

Levels are computed from total XP; UserProfile.current_level is kept in step.
"""
from datetime import timedelta

from django.db.models import F
from django.utils import timezone

BASE_XP_CORRECT = 10
XP_WRONG = 2
WEAK_SPOT_BONUS = 10
MAX_COMBO_STEPS = 10  # combo bonus stops growing here (x2.0)
COMBO_WINDOW = timedelta(minutes=30)  # a longer gap between answers breaks the combo
WEAK_SPOT_MIN_GAP = timedelta(hours=1)

# (first level of the rank, rank name)
RANKS = [(1, "Rookie"), (3, "Lifter"), (6, "Regular"), (10, "Athlete"), (15, "Champion"), (21, "Legend")]


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------
def xp_to_reach(level: int) -> int:
    """Total XP needed to be at `level`. Each level costs 50 XP more than the last, from 100."""
    n = max(level, 1) - 1
    return 100 * n + 25 * n * (n - 1)


def rank_for_level(level: int) -> str:
    name = RANKS[0][1]
    for first_level, rank in RANKS:
        if level >= first_level:
            name = rank
    return name


def level_for_xp(total_xp: int) -> dict:
    total_xp = max(int(total_xp or 0), 0)
    level = 1
    while xp_to_reach(level + 1) <= total_xp:
        level += 1
    start, end = xp_to_reach(level), xp_to_reach(level + 1)
    into, span = total_xp - start, end - start
    return {
        "level": level,
        "rank": rank_for_level(level),
        "total_xp": total_xp,
        "xp_into_level": into,
        "xp_for_next_level": span,
        "progress_pct": round(100 * into / span),
    }


# ---------------------------------------------------------------------------
# Combo and weak spots
# ---------------------------------------------------------------------------
def combo_multiplier(combo_before: int) -> float:
    return round(1 + 0.1 * min(max(combo_before, 0), MAX_COMBO_STEPS), 1)


def current_combo(student, exclude_attempt_id=None, now=None) -> int:
    """Consecutive correct answers just before now, with no gap over COMBO_WINDOW."""
    from learning.models import QuizAttempt

    now = now or timezone.now()
    qs = QuizAttempt.objects.filter(student=student)
    if exclude_attempt_id:
        qs = qs.exclude(id=exclude_attempt_id)
    combo, newer = 0, now
    for is_correct, at in qs.order_by("-attempted_at").values_list("is_correct", "attempted_at")[:MAX_COMBO_STEPS + 5]:
        if newer - at > COMBO_WINDOW or not is_correct:
            break
        combo += 1
        newer = at
    return combo


def is_weak_spot_fixed(student, question, exclude_attempt_id=None, now=None) -> bool:
    """True when the student's last earlier attempt at this question was wrong, over an hour ago."""
    from learning.models import QuizAttempt

    now = now or timezone.now()
    qs = QuizAttempt.objects.filter(student=student, question=question)
    if exclude_attempt_id:
        qs = qs.exclude(id=exclude_attempt_id)
    previous = qs.order_by("-attempted_at").first()
    return bool(previous and not previous.is_correct and now - previous.attempted_at >= WEAK_SPOT_MIN_GAP)


def reward_for_attempt(is_correct: bool, combo_before: int, weak_spot_fixed: bool) -> dict:
    if not is_correct:
        return {
            "xp": XP_WRONG, "base_xp": XP_WRONG, "combo_bonus_xp": 0, "weak_spot_bonus_xp": 0,
            "combo": 0, "multiplier": 1.0, "weak_spot_fixed": False,
        }
    multiplier = combo_multiplier(combo_before)
    boosted = round(BASE_XP_CORRECT * multiplier)
    bonus = WEAK_SPOT_BONUS if weak_spot_fixed else 0
    return {
        "xp": boosted + bonus,
        "base_xp": BASE_XP_CORRECT,
        "combo_bonus_xp": boosted - BASE_XP_CORRECT,
        "weak_spot_bonus_xp": bonus,
        "combo": combo_before + 1,
        "multiplier": multiplier,
        "weak_spot_fixed": weak_spot_fixed,
    }


# ---------------------------------------------------------------------------
# Awarding
# ---------------------------------------------------------------------------
def award_xp(student, xp: int) -> dict:
    """
    Add XP to the student's profile and keep current_level in step.
    Returns level info plus whether the student levelled up. Safe without a profile.
    """
    profile = getattr(student, "profile", None)
    if profile is None or xp <= 0:
        info = level_for_xp(profile.total_xp if profile else 0)
        return {**info, "leveled_up": False}
    before = level_for_xp(profile.total_xp)["level"]
    type(profile).objects.filter(pk=profile.pk).update(total_xp=F("total_xp") + xp)
    profile.refresh_from_db(fields=["total_xp"])
    info = level_for_xp(profile.total_xp)
    if profile.current_level != info["level"]:
        profile.current_level = info["level"]
        profile.save(update_fields=["current_level"])
    return {**info, "leveled_up": info["level"] > before, "previous_level": before}


def reward_payload(reward, is_correct: bool) -> dict:
    """The reward fields the answer endpoints send to the page. Falls back to flat XP if rewards failed."""
    if not reward:
        return {"xp_earned": BASE_XP_CORRECT if is_correct else XP_WRONG}
    level = reward.get("level") or {}
    return {
        "xp_earned": reward["xp"],
        "combo": reward["combo"],
        "multiplier": reward["multiplier"],
        "combo_bonus_xp": reward["combo_bonus_xp"],
        "weak_spot_fixed": reward["weak_spot_fixed"],
        "weak_spot_bonus_xp": reward["weak_spot_bonus_xp"],
        "level": level.get("level"),
        "rank": level.get("rank"),
        "level_progress_pct": level.get("progress_pct"),
        "leveled_up": level.get("leveled_up", False),
    }


def progress_summary(student) -> dict:
    """Level, rank, XP, streak and combo for the 'me' endpoint and the dashboard."""
    from learning.models import BossBattle

    profile = getattr(student, "profile", None)
    info = level_for_xp(profile.total_xp if profile else 0)
    info.update({
        "daily_streak": profile.daily_streak if profile else 0,
        "combo": current_combo(student),
        "multiplier": combo_multiplier(current_combo(student)),
        "bosses_defeated": BossBattle.objects.filter(student=student, status="won").order_by().values("topic").distinct().count(),
    })
    return info
