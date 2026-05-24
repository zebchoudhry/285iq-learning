"""
Adaptive selector for mission-driven practice sessions.
Supports diagnostic, drill, mixed practice, and exam simulation intents.
"""
from typing import List, Optional

from learning.models import Question, QuizAttempt, QuestionStep, StudentSkillState, Topic
from learning.services.exam_board_scope import (
    filter_questions_for_exam_board,
    resolve_exam_board_id_for_student_subject,
)
from users.models import Student, StudentTopicPerformance


def select_practice_questions(
    student: Student,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    count: int = 6,
    intent: Optional[str] = None,
) -> List[int]:
    """
    Select questions for adaptive practice.

    Logic:
    - diagnostic: broad baseline across core skills.
    - drill: weakness-first, lower-mid difficulty.
    - mixed_practice: interleaved medium difficulty.
    - exam_sim: higher-mark / harder questions.
    - fallback: weakness-first adaptive blend.
    """
    recent_attempt_ids = list(
        QuizAttempt.objects.filter(student=student)
        .order_by("-attempted_at")[:10]
        .values_list("question_id", flat=True)
    )

    base_q = Question.objects.filter(is_active=True)
    if topic_id:
        base_q = base_q.filter(lesson__topic_id=topic_id)
    elif subject_id:
        base_q = base_q.filter(lesson__topic__subject_id=subject_id)

    subj_for_board = subject_id
    if subj_for_board is None and topic_id:
        t = Topic.objects.filter(id=topic_id).values_list("subject_id", flat=True).first()
        subj_for_board = t
    exam_board_id = None
    if subj_for_board:
        exam_board_id = resolve_exam_board_id_for_student_subject(student.id, subj_for_board)
    base_q = filter_questions_for_exam_board(base_q, exam_board_id)

    base_q = base_q.exclude(id__in=recent_attempt_ids)

    # Exclude questions linked to MASTERED skills (graduation)
    mastered_skill_ids = list(
        StudentSkillState.objects.filter(
            student=student, status='MASTERED'
        ).values_list("skill_id", flat=True)
    )
    if mastered_skill_ids:
        mastered_q_ids = list(
            QuestionStep.objects.filter(
                skill_id__in=mastered_skill_ids
            ).values_list("question_id", flat=True).distinct()
        )
        if mastered_q_ids:
            base_q = base_q.exclude(id__in=mastered_q_ids)

    # Intent-specific routing first.
    if intent == "diagnostic":
        return _select_diagnostic_questions(base_q, count=count)
    if intent == "exam_sim":
        return _select_exam_sim_questions(base_q, count=count)
    if intent == "mixed_practice":
        return _select_mixed_questions(base_q, count=count)
    if intent == "drill":
        return _select_drill_questions(
            base_q=base_q,
            student=student,
            subject_id=subject_id,
            topic_id=topic_id,
            count=count,
        )

    selected_ids: List[int] = []

    # 1) Skill-based: weakest skills via QuestionStep (exclude MASTERED)
    SKILLS_ACTIVE = ['NEW', 'LEARNING', 'IMPROVING', 'AT_RISK']
    skill_states = StudentSkillState.objects.filter(
        student=student, attempts__gte=3, status__in=SKILLS_ACTIVE
    ).order_by("rolling_accuracy")[:2]

    if skill_states.exists():
        weak_skills = [s.skill_id for s in skill_states]
        skill_question_ids = list(
            QuestionStep.objects.filter(skill_id__in=weak_skills)
            .values_list("question_id", flat=True)
            .distinct()
        )
        if skill_question_ids:
            skill_questions = base_q.filter(
                id__in=skill_question_ids, difficulty_level__lte=3
            ).order_by("?")[:4]
            selected_ids.extend(skill_questions.values_list("id", flat=True))

    # 2) Topic-based weakness: prefer questions from weakest topics
    if len(selected_ids) < count:
        weak_topic_ids = _weak_topic_ids(student, subject_id=subject_id, topic_id=topic_id)
        if weak_topic_ids:
            remaining = count - len(selected_ids)
            weak_qs = (
                base_q.filter(lesson__topic_id__in=weak_topic_ids)
                .exclude(id__in=selected_ids)
                .filter(difficulty_level__lte=3)
                .order_by("?")[:remaining]
            )
            selected_ids.extend(weak_qs.values_list("id", flat=True))

    # 3) Fill to count with any suitable questions
    if len(selected_ids) < count:
        remaining = count - len(selected_ids)
        fallback = (
            base_q.filter(difficulty_level__in=[1, 2, 3])
            .exclude(id__in=selected_ids)
            .order_by("?")[:remaining]
        )
        selected_ids.extend(fallback.values_list("id", flat=True))

    return list(selected_ids)[:count]


def _select_diagnostic_questions(base_q, count: int) -> List[int]:
    """
    Diagnostic should cover breadth first:
    - sample across lower-mid-high difficulty
    - avoid over-indexing to one narrow weakness
    """
    selected: List[int] = []
    buckets = [
        base_q.filter(difficulty_level__in=[1, 2]).order_by("?")[: max(1, count // 3)],
        base_q.filter(difficulty_level=3).order_by("?")[: max(1, count // 3)],
        base_q.filter(difficulty_level__gte=4).order_by("?")[: max(1, count // 4)],
    ]
    for qs in buckets:
        selected.extend(qs.values_list("id", flat=True))
    if len(selected) < count:
        fill = (
            base_q.exclude(id__in=selected)
            .order_by("?")[: count - len(selected)]
        )
        selected.extend(fill.values_list("id", flat=True))
    return list(dict.fromkeys(selected))[:count]


def _select_exam_sim_questions(base_q, count: int) -> List[int]:
    qs = (
        base_q.filter(difficulty_level__gte=3)
        .order_by("-marks_available", "-difficulty_level", "?")[:count]
    )
    ids = list(qs.values_list("id", flat=True))
    if len(ids) < count:
        fill = base_q.exclude(id__in=ids).order_by("?")[: count - len(ids)]
        ids.extend(fill.values_list("id", flat=True))
    return ids[:count]


def _select_mixed_questions(base_q, count: int) -> List[int]:
    qs = base_q.filter(difficulty_level__in=[2, 3, 4]).order_by("?")[:count]
    ids = list(qs.values_list("id", flat=True))
    if len(ids) < count:
        fill = base_q.exclude(id__in=ids).order_by("?")[: count - len(ids)]
        ids.extend(fill.values_list("id", flat=True))
    return ids[:count]


def _select_drill_questions(
    base_q,
    student: Student,
    subject_id: Optional[int],
    topic_id: Optional[int],
    count: int,
) -> List[int]:
    selected_ids: List[int] = []
    weak_topic_ids = _weak_topic_ids(student, subject_id=subject_id, topic_id=topic_id)
    if weak_topic_ids:
        weak_qs = (
            base_q.filter(lesson__topic_id__in=weak_topic_ids, difficulty_level__lte=3)
            .order_by("?")[:count]
        )
        selected_ids.extend(weak_qs.values_list("id", flat=True))
    if len(selected_ids) < count:
        fill = (
            base_q.filter(difficulty_level__lte=3)
            .exclude(id__in=selected_ids)
            .order_by("?")[: count - len(selected_ids)]
        )
        selected_ids.extend(fill.values_list("id", flat=True))
    return selected_ids[:count]


def _weak_topic_ids(
    student: Student,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    min_attempts: int = 3,
    max_topics: int = 3,
) -> List[int]:
    """Return topic IDs where student has lowest success rate (weak areas)."""
    qs = StudentTopicPerformance.objects.filter(
        student=student, questions_attempted__gte=min_attempts
    ).select_related("topic", "topic__subject")

    if topic_id:
        qs = qs.filter(topic_id=topic_id)
    elif subject_id:
        qs = qs.filter(topic__subject_id=subject_id)

    perfs = list(qs)
    perfs.sort(
        key=lambda p: (
            (p.questions_correct / p.questions_attempted)
            if p.questions_attempted
            else 1.0
        )
    )
    return [p.topic_id for p in perfs[:max_topics] if p.topic_id]
