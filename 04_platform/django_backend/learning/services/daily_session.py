"""
"Start your 10 minutes": picks one short session for a student, so they never have to decide
where to begin.

The mix, in priority order:
  1. questions they got wrong that are due back (mistake bank)
  2. flashcards due today (spaced repetition)
  3. fresh questions from their weakest topic, or a topic they have not tried yet

It reads existing data only. Answers go through the normal attempt and flashcard-review
endpoints, so XP, mistakes and card scheduling all work as they do everywhere else.
"""
import random
from typing import Any, Dict, List, Optional, Set

from django.db.models import Q
from django.utils import timezone

from learning.models import (
    Flashcard,
    MistakeBankItem,
    Question,
    StudentExamSettings,
    StudentFlashcardProgress,
    Topic,
)
from learning.services.topic_mastery import topic_mastery
from learning.serializers import QuestionForQuizSerializer

DEFAULT_SIZE = 8
MAX_MISTAKES = 4
MAX_CARDS = 3
SECONDS_PER_ITEM = {"question": 60, "flashcard": 20}


def _question_item(question: Question, source: str, mistake_id: Optional[int] = None) -> Dict[str, Any]:
    topic = question.lesson.topic
    return {
        "kind": "question",
        "source": source,  # "mistake" | "weak_topic" | "new_topic"
        "mistake_id": mistake_id,
        "topic": topic.name,
        "subject": topic.subject.display_name,
        "question": QuestionForQuizSerializer(question).data,
    }


def _card_item(card: Flashcard) -> Dict[str, Any]:
    return {
        "kind": "flashcard",
        "source": "due_card",
        "id": card.id,
        "topic": card.topic.name,
        "subject": card.topic.subject.display_name,
        "front": card.front,
        "back": card.back,
    }


def _mistake_items(student, limit: int) -> List[Dict[str, Any]]:
    now = timezone.now()
    rows = (
        MistakeBankItem.objects.filter(student=student, status__in=("active", "retrying"))
        .filter(Q(next_review_at__isnull=True) | Q(next_review_at__lte=now))
        .filter(question__is_active=True)
        .select_related("question__lesson__topic__subject")
        .order_by("next_review_at", "-last_seen_at")
    )
    items, seen = [], set()
    for row in rows:
        if row.question_id in seen:
            continue
        seen.add(row.question_id)
        items.append(_question_item(row.question, "mistake", row.id))
        if len(items) == limit:
            break
    return items


def _card_items(student, limit: int) -> List[Dict[str, Any]]:
    today = timezone.now().date()
    due = (
        StudentFlashcardProgress.objects.filter(
            student=student, due_date__lte=today, flashcard__is_active=True,
            flashcard__topic__is_active=True,
        )
        .select_related("flashcard__topic__subject")
        .order_by("due_date", "id")[:limit]
    )
    return [_card_item(p.flashcard) for p in due]


MAX_FOCUS_TOPICS = 3
UNTRIED_WEIGHT = 0.4
GRADUATED_WEIGHT = 0.08
URGENCY_HORIZON_DAYS = 180


def _urgency_by_subject(student) -> Dict[int, float]:
    """1.0 when no exam is near, rising to 2.0 as a subject's exam date approaches."""
    today = timezone.now().date()
    out: Dict[int, float] = {}
    for st in StudentExamSettings.objects.filter(student=student):
        days = (st.exam_date - today).days
        if 0 <= days <= URGENCY_HORIZON_DAYS:
            out[st.subject_id] = 1.0 + (1.0 - days / URGENCY_HORIZON_DAYS)
        else:
            out[st.subject_id] = 1.0
    return out


def plan_topics(student) -> List[Dict[str, Any]]:
    """
    Which topics deserve today's fresh questions, and how much of the session each gets.

    The weight of a topic comes from recent accuracy, so it falls as the student improves:
    a weak topic keeps coming back, in larger shares, until they have answered it well enough
    to "graduate" (see topic_mastery), after which it only gets a light refresher. Untried topics
    get a middling weight so new ground is still covered. Subjects with a nearer exam date are
    weighted up. Only topics that have questions are considered.
    """
    topics = list(
        Topic.objects.filter(
            is_active=True, lessons__is_active=True, lessons__questions__is_active=True
        ).select_related("subject").distinct()
    )
    if not topics:
        return []
    with_exams = set(StudentExamSettings.objects.filter(student=student).values_list("subject_id", flat=True))
    if with_exams:  # a student who set exam dates is revising those subjects
        scoped = [t for t in topics if t.subject_id in with_exams]
        topics = scoped or topics
    mastery = topic_mastery(student, [t.id for t in topics])
    urgency = _urgency_by_subject(student)

    plan = []
    for t in topics:
        m = mastery[t.id]
        if m["accuracy"] is None:
            weight, source = UNTRIED_WEIGHT, "new_topic"
        elif m["graduated"]:
            weight, source = GRADUATED_WEIGHT, "maintenance"
        else:
            weight, source = (1.0 - m["accuracy"]) ** 1.5 + 0.05, "weak_topic"
        weight *= urgency.get(t.subject_id, 1.0)
        plan.append({"topic": t, "source": source, "weight": weight, "accuracy": m["accuracy"]})
    plan.sort(key=lambda p: (-p["weight"], p["topic"].subject_id, p["topic"].order, p["topic"].id))
    return plan[:MAX_FOCUS_TOPICS]


def _allocate(plan: List[Dict[str, Any]], total: int) -> List[int]:
    """Split `total` questions across the planned topics by weight (largest remainder, min 1 each)."""
    n = len(plan)
    if n == 0 or total <= 0:
        return [0] * n
    shares = [0] * n
    if total >= n:
        shares = [1] * n
        total -= n
    weight_sum = sum(p["weight"] for p in plan) or 1.0
    raw = [total * p["weight"] / weight_sum for p in plan]
    whole = [int(r) for r in raw]
    leftover = total - sum(whole)
    order = sorted(range(n), key=lambda i: raw[i] - whole[i], reverse=True)
    for i in order[:leftover]:
        whole[i] += 1
    return [shares[i] + whole[i] for i in range(n)]


def _fresh_questions(student, topic: Topic, exclude: Set[int], count: int) -> List[Question]:
    from learning.models import QuizAttempt

    answered = set(
        QuizAttempt.objects.filter(student=student, question__lesson__topic=topic)
        .values_list("question_id", flat=True)
    )
    base = Question.objects.filter(
        lesson__topic=topic, lesson__is_active=True, is_active=True, is_shared=True
    ).exclude(id__in=exclude).select_related("lesson__topic__subject")
    ids = list(base.values_list("id", flat=True))
    rng = random.Random(f"{student.pk}-{topic.pk}-{timezone.now().date().isoformat()}")
    rng.shuffle(ids)
    ids.sort(key=lambda i: i in answered)  # stable: unseen questions first
    picked = ids[:count]
    by_id = {q.id: q for q in base.filter(id__in=picked)}
    return [by_id[i] for i in picked if i in by_id]


GYM_LABELS = {
    "instruction": "building basics",
    "guided_practice": "easier questions first",
    "drill": "drilling the weak spots",
    "mixed_practice": "mixed difficulty",
    "exam_sim": "exam-level questions",
    "mastery_maintenance": "keeping it fresh",
}


def _gym_questions(student, topic: Topic, exclude: Set[int], count: int):
    """
    Progressive overload: the topic's gym mode (driven by accuracy, with hysteresis so it does not
    flip on one answer) decides how hard the questions are. Weak topics get easier, guided
    questions; strong ones step up to mixed and exam-level.
    """
    from learning.services.gym_controller import decide_gym_mode

    try:
        result = decide_gym_mode(student.id, topic.id)
    except Exception:  # never let the picker fail the whole session
        return [], None
    mode = result.get("mode")
    ids = [row["id"] for row in result.get("content", {}).get("items", []) if "id" in row and "title" not in row]
    ids = [i for i in ids if i not in exclude]
    base = Question.objects.filter(
        id__in=ids, is_active=True, is_shared=True, lesson__is_active=True
    ).select_related("lesson__topic__subject")
    by_id = {q.id: q for q in base}
    return [by_id[i] for i in ids if i in by_id][:count], mode


def build_daily_session(student, size: int = DEFAULT_SIZE) -> Dict[str, Any]:
    size = max(3, min(int(size), 15))
    items: List[Dict[str, Any]] = []

    items += _mistake_items(student, min(MAX_MISTAKES, size))
    items += _card_items(student, min(MAX_CARDS, size - len(items)))

    plan = plan_topics(student)
    focus_name = None
    gym_mode = None
    focus_topics: List[Dict[str, Any]] = []
    if plan and len(items) < size:
        used = {i["question"]["id"] for i in items if i["kind"] == "question"}
        need = size - len(items)
        shares = _allocate(plan, need)
        picked_by_topic: List[List[Question]] = []
        for entry, share in zip(plan, shares):
            picked, mode = _gym_questions(student, entry["topic"], used, share)
            if len(picked) < share:
                picked += _fresh_questions(student, entry["topic"], used | {q.id for q in picked}, share - len(picked))
            used |= {q.id for q in picked}
            picked_by_topic.append(picked)
            if gym_mode is None:
                gym_mode = mode
        # a topic with too few questions hands its unused share to the others
        shortfall = need - sum(len(p) for p in picked_by_topic)
        for entry, picked in zip(plan, picked_by_topic):
            if shortfall <= 0:
                break
            extra = _fresh_questions(student, entry["topic"], used, shortfall)
            picked += extra
            used |= {q.id for q in extra}
            shortfall -= len(extra)
        for entry, picked in zip(plan, picked_by_topic):
            for q in picked:
                items.append(_question_item(q, entry["source"]))
            if picked:
                focus_topics.append({
                    "topic": entry["topic"].name,
                    "subject": entry["topic"].subject.display_name,
                    "questions": len(picked),
                    "accuracy": None if entry["accuracy"] is None else round(entry["accuracy"] * 100),
                    "reason": entry["source"],
                })
        if focus_topics:
            focus_name = focus_topics[0]["topic"]

    # questions first-in-first-out, but spread flashcards through the session so it is not two blocks
    questions = [i for i in items if i["kind"] == "question"]
    cards = [i for i in items if i["kind"] == "flashcard"]
    ordered: List[Dict[str, Any]] = []
    step = max(1, len(questions) // (len(cards) + 1)) if cards else 0
    qi = 0
    while questions or cards:
        if questions:
            ordered.append(questions.pop(0))
            qi += 1
        if cards and step and qi % step == 0:
            ordered.append(cards.pop(0))
        if not questions:
            ordered.extend(cards)
            cards = []

    n_mistakes = sum(1 for i in ordered if i.get("source") == "mistake")
    n_cards = sum(1 for i in ordered if i["kind"] == "flashcard")
    parts = []
    if n_mistakes:
        parts.append(f"{n_mistakes} question{'s' if n_mistakes != 1 else ''} you missed before")
    if n_cards:
        parts.append(f"{n_cards} flashcard{'s' if n_cards != 1 else ''} due today")
    for ft in focus_topics:
        label = {
            "weak_topic": f"{ft['questions']} on {ft['topic']} (needs work, {ft['accuracy']}% lately)" if ft["accuracy"] is not None else f"{ft['questions']} on {ft['topic']}",
            "new_topic": f"{ft['questions']} new on {ft['topic']}",
            "maintenance": f"{ft['questions']} refresher on {ft['topic']}",
        }[ft["reason"]]
        parts.append(label)
    seconds = sum(SECONDS_PER_ITEM[i["kind"]] for i in ordered)

    return {
        "count": len(ordered),
        "minutes": max(1, round(seconds / 60)) if ordered else 0,
        "summary": ", ".join(parts),
        "focus_topic": focus_name,
        "focus_topics": focus_topics,
        "difficulty": GYM_LABELS.get(gym_mode) if gym_mode else None,
        "items": ordered,
    }
