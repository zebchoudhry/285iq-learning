import json
import re

from learning.models import Lesson, MultipleChoiceOption, Question, Topic
from learning.services.llm_service import generate as llm_generate


def _extract_json_array(text):
    if not text:
        return []
    cleaned = text.strip()
    # strip fenced blocks if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        data = json.loads(cleaned[start : end + 1])
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _get_or_create_generated_lesson(topic):
    lesson = (
        Lesson.objects.filter(topic=topic, title__iexact="Generated Practice", is_active=True)
        .order_by("order")
        .first()
    )
    if lesson:
        return lesson
    return Lesson.objects.create(
        topic=topic,
        title="Generated Practice",
        content=f"Auto-generated practice for {topic.name}.",
        estimated_duration=20,
        lesson_type="practice",
        difficulty_level=2,
        key_skills=[],
        order=999,
        is_active=True,
    )


def generate_questions(topic_id, mode, difficulty=2, count=6, exam_board=None):
    """
    Generate questions for a topic and return created question IDs.
    Returns [] on failure so callers can fall back safely.
    """
    try:
        topic = Topic.objects.select_related("subject").get(id=topic_id, is_active=True)
    except Topic.DoesNotExist:
        return []

    prompt = (
        f"Generate {count} GCSE {topic.subject.display_name} questions on {topic.name}. "
        f"Mode: {mode}. Difficulty: {difficulty}/5. "
        "Return only JSON array with keys: question_text, correct_answer, explanation, "
        "question_type (short_answer or multiple_choice), difficulty_level, options (optional list of strings)."
    )
    if exam_board:
        prompt += f" Exam board: {exam_board}."

    try:
        raw = llm_generate(prompt=prompt, max_tokens=1200, temperature=0.2)
    except Exception:
        return []

    items = _extract_json_array(raw)
    if not items:
        return []

    lesson = _get_or_create_generated_lesson(topic)
    created_ids = []
    for item in items[: max(1, int(count))]:
        if not isinstance(item, dict):
            continue
        qtext = (item.get("question_text") or "").strip()
        ans = (item.get("correct_answer") or "").strip()
        expl = (item.get("explanation") or "").strip()
        qtype = item.get("question_type") or "short_answer"
        level = item.get("difficulty_level") or difficulty
        if not qtext or not ans:
            continue
        q = Question.objects.create(
            lesson=lesson,
            question_text=qtext,
            correct_answer=ans,
            explanation=expl,
            question_type=qtype if qtype in dict(Question.QUESTION_TYPE_CHOICES) else "short_answer",
            difficulty_level=max(1, min(5, int(level))),
            source="llm_generated",
            is_active=True,
        )
        created_ids.append(q.id)

        if q.question_type == "multiple_choice":
            options = item.get("options") or []
            if isinstance(options, list):
                saw_correct = False
                for idx, text in enumerate(options[:6]):
                    opt_text = str(text).strip()
                    if not opt_text:
                        continue
                    is_correct = (opt_text.lower() == ans.lower()) and not saw_correct
                    if is_correct:
                        saw_correct = True
                    MultipleChoiceOption.objects.create(
                        question=q,
                        option_text=opt_text,
                        is_correct=is_correct,
                        order=idx,
                    )
                if not saw_correct:
                    MultipleChoiceOption.objects.create(
                        question=q,
                        option_text=ans,
                        is_correct=True,
                        order=99,
                    )

    return created_ids
