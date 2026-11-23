"""
Boss battles: a fixed run of questions on one topic.

  - correct answer: damages the boss (10, +2 per answer in the current combo up to +10,
    and +10 'critical hit' on one of the student's weak questions)
  - wrong answer: the boss heals 8 and the combo resets
  - the boss is beaten when its HP reaches 0; if the questions run out first it escapes

At about 70% accuracy a student wins, so a win means the topic is in good shape.
"""
import random

from django.utils import timezone

from learning.models import BossBattle, Question, QuizAttempt
from learning.services import gamification

BOSS_HP = 100
ROUNDS = 15
MIN_QUESTIONS = 5
MAX_WEAK_QUESTIONS = 5
BASE_DAMAGE = 10
COMBO_DAMAGE = 2
MAX_COMBO_DAMAGE_STEPS = 5
CRITICAL_BONUS = 10
HEAL_ON_WRONG = 8
WIN_BONUS_XP = 50

BOSS_SUFFIXES = ["Titan", "Golem", "Wraith", "Hydra", "Behemoth", "Phantom", "Colossus"]


class BossError(Exception):
    """A battle request that cannot be carried out; the message is safe to show."""


def boss_name_for(topic) -> str:
    return f"{topic.name} {BOSS_SUFFIXES[topic.id % len(BOSS_SUFFIXES)]}"


def weak_and_seen_question_ids(student, topic):
    """(weak ids, seen ids): weak = last attempt wrong or flagged for review."""
    latest, flagged, seen = {}, set(), set()
    rows = (
        QuizAttempt.objects.filter(student=student, question__lesson__topic=topic)
        .order_by("-attempted_at")
        .values_list("question_id", "is_correct", "needs_review")[:3000]
    )
    for question_id, is_correct, needs_review in rows:
        seen.add(question_id)
        latest.setdefault(question_id, is_correct)  # first row seen is the most recent
        if needs_review:
            flagged.add(question_id)
    weak = {q for q, ok in latest.items() if not ok} | flagged
    return weak, seen


def start_battle(student, topic, rng=None) -> BossBattle:
    """Resume the student's active battle on this topic, or start a new one."""
    existing = BossBattle.objects.filter(student=student, topic=topic, status="active").first()
    if existing:
        return existing
    rng = rng or random.Random()

    active_ids = set(
        Question.objects.filter(lesson__topic=topic, lesson__is_active=True, is_active=True)
        .values_list("id", flat=True)
    )
    weak, seen = weak_and_seen_question_ids(student, topic)
    weak &= active_ids
    chosen_weak = rng.sample(sorted(weak), min(len(weak), MAX_WEAK_QUESTIONS))

    others = sorted(active_ids - set(chosen_weak))
    rng.shuffle(others)
    others.sort(key=lambda q: q in seen)  # unseen first (stable, keeps the shuffle within each group)
    picked = chosen_weak + others[: max(0, ROUNDS - len(chosen_weak))]
    if len(picked) < MIN_QUESTIONS:
        raise BossError("This topic doesn't have enough questions for a boss battle yet.")
    rng.shuffle(picked)

    return BossBattle.objects.create(
        student=student,
        topic=topic,
        boss_name=boss_name_for(topic),
        max_hp=BOSS_HP,
        hp=BOSS_HP,
        max_rounds=len(picked),
        question_ids=picked,
        weak_question_ids=chosen_weak,
    )


def current_question_id(battle: BossBattle):
    if battle.status != "active" or battle.answered >= len(battle.question_ids):
        return None
    return battle.question_ids[battle.answered]


def apply_answer(battle: BossBattle, question_id: int, is_correct: bool) -> dict:
    """Update the fight for one answer. The caller has already recorded the attempt."""
    if battle.status != "active":
        raise BossError("This battle is over.")
    if current_question_id(battle) != question_id:
        raise BossError("That isn't the current question in this battle.")

    combo_before = battle.combo
    damage = healed = 0
    critical = False
    if is_correct:
        damage = BASE_DAMAGE + COMBO_DAMAGE * min(combo_before, MAX_COMBO_DAMAGE_STEPS)
        if question_id in battle.weak_question_ids:
            critical = True
            damage += CRITICAL_BONUS
        battle.hp = max(0, battle.hp - damage)
        battle.correct_count += 1
        battle.combo = combo_before + 1
        battle.best_combo = max(battle.best_combo, battle.combo)
    else:
        healed = min(HEAL_ON_WRONG, battle.max_hp - battle.hp)
        battle.hp += healed
        battle.combo = 0
    battle.answered += 1

    result = {"damage": damage, "healed": healed, "critical": critical, "finished": False}
    if battle.hp == 0:
        battle.status = "won"
    elif battle.answered >= battle.max_rounds:
        battle.status = "escaped"
    finished = battle.status != "active"
    if finished:
        battle.finished_at = timezone.now()
        result["finished"] = True
        if battle.status == "won":
            battle.xp_awarded = WIN_BONUS_XP
    battle.save()
    if finished and battle.status == "won":
        result["level"] = gamification.award_xp(battle.student, WIN_BONUS_XP)
        _award_boss_achievements(battle.student)  # after the save, so this win is counted
    return result


def _award_boss_achievements(student):
    from users.achievements import award_achievement

    award_achievement(student, "boss_slayer", "Boss Slayer", "Defeat your first topic boss.", "⚔️")
    defeated = BossBattle.objects.filter(student=student, status="won").order_by().values("topic").distinct().count()
    if defeated >= 5:
        award_achievement(student, "boss_hunter", "Boss Hunter", "Defeat the boss in 5 different topics.", "🏆")


def battle_state(battle: BossBattle) -> dict:
    return {
        "id": battle.id,
        "boss_name": battle.boss_name,
        "topic_id": battle.topic_id,
        "topic_name": battle.topic.name,
        "hp": battle.hp,
        "max_hp": battle.max_hp,
        "round": min(battle.answered + 1, battle.max_rounds),
        "max_rounds": battle.max_rounds,
        "answered": battle.answered,
        "correct_count": battle.correct_count,
        "combo": battle.combo,
        "best_combo": battle.best_combo,
        "status": battle.status,
        "xp_awarded": battle.xp_awarded,
    }
