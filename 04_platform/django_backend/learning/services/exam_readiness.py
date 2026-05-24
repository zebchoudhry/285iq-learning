from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from dashboard.models import MockExamAttempt
from learning.models import (
    Lesson,
    MistakeBankItem,
    QuizAttempt,
    StudentExamSettings,
    StudentProgress,
    StudentSkillState,
    Subject,
    Topic,
)


def _clamp(value, low=0, high=100):
    return max(low, min(high, int(round(value))))


def _status_from_score(score):
    if score >= 85:
        return "exam_ready"
    if score >= 70:
        return "almost_ready"
    if score >= 45:
        return "building"
    return "not_ready"


def _estimate_grade_from_accuracy(accuracy):
    if accuracy >= 85:
        return 8
    if accuracy >= 75:
        return 7
    if accuracy >= 65:
        return 6
    if accuracy >= 55:
        return 5
    if accuracy >= 45:
        return 4
    if accuracy >= 35:
        return 3
    return 2


def build_subject_exam_readiness(student, subject):
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_lessons = Lesson.objects.filter(topic__subject=subject, is_active=True).count()
    completed_lessons = StudentProgress.objects.filter(
        student=student,
        lesson__topic__subject=subject,
        is_completed=True,
    ).count()
    attempted_topics = (
        QuizAttempt.objects.filter(student=student, question__lesson__topic__subject=subject)
        .values("question__lesson__topic_id")
        .distinct()
        .count()
    )
    total_topics = Topic.objects.filter(subject=subject, is_active=True).count()

    lesson_coverage = (100.0 * completed_lessons / total_lessons) if total_lessons else 0.0
    topic_coverage = (100.0 * attempted_topics / total_topics) if total_topics else 0.0
    coverage_score = (lesson_coverage * 0.6) + (topic_coverage * 0.4)

    recent_attempts = QuizAttempt.objects.filter(
        student=student,
        question__lesson__topic__subject=subject,
        attempted_at__gte=month_ago,
    )
    recent_count = recent_attempts.count()
    recent_correct = recent_attempts.filter(is_correct=True).count()
    recent_accuracy = (100.0 * recent_correct / recent_count) if recent_count else 0.0

    active_mistakes = MistakeBankItem.objects.filter(
        student=student,
        topic__subject=subject,
        status__in=["active", "retrying"],
    ).count()
    mastered_mistakes = MistakeBankItem.objects.filter(
        student=student,
        topic__subject=subject,
        status="mastered",
    ).count()
    mistake_total = active_mistakes + mastered_mistakes
    weak_recovery_score = (
        100.0 * mastered_mistakes / mistake_total
        if mistake_total
        else (80.0 if recent_count >= 10 else 40.0)
    )
    active_mistake_penalty = min(25, active_mistakes * 4)

    mock_attempts = MockExamAttempt.objects.filter(
        student=student,
        mock_exam__subject=subject,
        status="completed",
        exam_conditions=True,
    )
    latest_mock = mock_attempts.order_by("-completed_at", "-started_at").first()
    mock_score = latest_mock.percentage_score if latest_mock and latest_mock.percentage_score is not None else 0.0

    sessions_7d = student.study_sessions.filter(subject=subject, started_at__gte=week_ago).count()
    consistency_score = min(100.0, sessions_7d * 25.0)

    readiness_score = (
        coverage_score * 0.35
        + recent_accuracy * 0.25
        + weak_recovery_score * 0.20
        + mock_score * 0.10
        + consistency_score * 0.10
        - active_mistake_penalty
    )
    readiness_score = _clamp(readiness_score)
    status = _status_from_score(readiness_score)

    setting = StudentExamSettings.objects.filter(student=student, subject=subject).first()
    target_grade = setting.target_grade if setting else 5
    predicted_grade = (
        latest_mock.predicted_grade
        if latest_mock and latest_mock.predicted_grade
        else _estimate_grade_from_accuracy(recent_accuracy)
    )

    unlock_requirements = []
    if coverage_score < 70:
        needed_topics = max(1, int(round(max(0, total_topics - attempted_topics))))
        unlock_requirements.append(f"Cover more of the specification: attempt practice across {needed_topics} more topic(s).")
    if recent_count < 20:
        unlock_requirements.append(f"Complete {20 - recent_count} more recent practice question(s) in this subject.")
    elif recent_accuracy < 70:
        unlock_requirements.append("Reach 70%+ recent accuracy in mixed practice.")
    if active_mistakes > 0:
        unlock_requirements.append(f"Clear or master {active_mistakes} active mistake-bank item(s).")
    if mock_score < 60:
        unlock_requirements.append("Complete at least one timed mock-style paper at 60%+.")
    if sessions_7d < 2:
        unlock_requirements.append("Complete 2 focused study sessions this week.")

    if not unlock_requirements and readiness_score < 85:
        unlock_requirements.append("Complete one more mixed practice session to confirm readiness.")

    return {
        "subject_id": subject.id,
        "subject_name": subject.display_name,
        "score": readiness_score,
        "status": status,
        "exam_arena_unlocked": status == "exam_ready",
        "target_grade": target_grade,
        "predicted_grade": predicted_grade,
        "metrics": {
            "coverage_score": _clamp(coverage_score),
            "lesson_coverage": _clamp(lesson_coverage),
            "topic_coverage": _clamp(topic_coverage),
            "recent_accuracy": _clamp(recent_accuracy),
            "recent_attempts": recent_count,
            "weak_recovery_score": _clamp(weak_recovery_score),
            "active_mistakes": active_mistakes,
            "mastered_mistakes": mastered_mistakes,
            "latest_mock_score": _clamp(mock_score),
            "sessions_last_7_days": sessions_7d,
            "consistency_score": _clamp(consistency_score),
        },
        "unlock_requirements": unlock_requirements[:5],
        "recommended_next_url": f"/practice/{subject.id}/" if status != "exam_ready" else "/mock-tests/",
    }


def build_exam_readiness(student):
    subjects = Subject.objects.filter(is_active=True).annotate(topic_count=Count("topics")).order_by("display_name")
    return [build_subject_exam_readiness(student, subject) for subject in subjects]
