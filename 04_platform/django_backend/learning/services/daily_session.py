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
    StudentFlashcardProgress,
    Topic,
)
from users.models import StudentTopicPerformance
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


def _focus_topic(student) -> Optional[Dict[str, Any]]:
    """Weakest topic with enough attempts to judge; otherwise one the student has not tried."""
    perfs = list(
        StudentTopicPerformance.objects.filter(
            student=student, questions_attempted__gte=3, topic__is_active=True
        ).select_related("topic")
    )
    if perfs:
        perfs.sort(key=lambda p: p.questions_correct / p.questions_attempted)
        worst = perfs[0]
        if worst.questions_correct / worst.questions_attempted < 0.8:
            return {"topic": worst.topic, "source": "weak_topic"}
    tried = set(
        StudentTopicPerformance.objects.filter(student=student).values_list("topic_id", flat=True)
    )
    fresh = Topic.objects.filter(is_active=True, lessons__questions__is_active=True).exclude(id__in=tried)
    topic = fresh.order_by("subject_id", "order", "id").distinct().first()
    if topic:
        return {"topic": topic, "source": "new_topic"}
    if perfs:  # everything tried and fine: keep practising the weakest anyway
        return {"topic": perfs[0].topic, "source": "weak_topic"}
    return None


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

    focus = _focus_topic(student)
    focus_name = None
    gym_mode = None
    if focus and len(items) < size:
        used = {i["question"]["id"] for i in items if i["kind"] == "question"}
        need = size - len(items)
        picked, gym_mode = _gym_questions(student, focus["topic"], used, need)
        if len(picked) < need:  # gym mode had too few (or only lessons): top up with unseen questions
            used |= {q.id for q in picked}
            picked += _fresh_questions(student, focus["topic"], used, need - len(picked))
        for q in picked:
            items.append(_question_item(q, focus["source"]))
        focus_name = focus["topic"].name

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
    n_new = len(ordered) - n_mistakes - n_cards
    parts = []
    if n_mistakes:
        parts.append(f"{n_mistakes} question{'s' if n_mistakes != 1 else ''} you missed before")
    if n_cards:
        parts.append(f"{n_cards} flashcard{'s' if n_cards != 1 else ''} due today")
    if n_new:
        parts.append(f"{n_new} on {focus_name}" if focus_name else f"{n_new} new")
    seconds = sum(SECONDS_PER_ITEM[i["kind"]] for i in ordered)

    return {
        "count": len(ordered),
        "minutes": max(1, round(seconds / 60)) if ordered else 0,
        "summary": ", ".join(parts),
        "focus_topic": focus_name,
        "difficulty": GYM_LABELS.get(gym_mode) if gym_mode else None,
        "items": ordered,
    }
