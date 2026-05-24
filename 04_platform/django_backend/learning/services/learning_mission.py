from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone

from learning.models import Question, QuestionStep, StudentExamSettings, StudentSkillState


@dataclass
class MissionContext:
    task_type: str
    subject_id: Optional[int]
    topic_id: Optional[int]
    skill_codes: List[str]
    reason: str
    parent_reason: str
    risk_level: str
    target_grade_gap: int
    cta_url: str
    diagnostic_required: bool
    diagnostic_progress: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "subject_id": self.subject_id,
            "topic_id": self.topic_id,
            "skill_codes": self.skill_codes,
            "reason": self.reason,
            "parent_reason": self.parent_reason,
            "risk_level": self.risk_level,
            "target_grade_gap": self.target_grade_gap,
            "cta_url": self.cta_url,
            "diagnostic_required": self.diagnostic_required,
            "diagnostic_progress": self.diagnostic_progress,
        }


def _risk_from_gap(grade_gap: int) -> str:
    if grade_gap <= 0:
        return "on_track"
    if grade_gap == 1:
        return "watch"
    return "at_risk"


def _estimate_predicted_grade(student, subject_id: Optional[int]) -> int:
    if not subject_id:
        return 5
    attempts = list(
        student.quiz_attempts.filter(question__lesson__topic__subject_id=subject_id)
        .order_by("-attempted_at")[:30]
    )
    total = len(attempts)
    if total == 0:
        return 5
    correct = sum(1 for attempt in attempts if attempt.is_correct)
    pct = 100.0 * correct / total
    if pct >= 85:
        return 8
    if pct >= 75:
        return 7
    if pct >= 65:
        return 6
    if pct >= 55:
        return 5
    if pct >= 45:
        return 4
    return 3


def _diagnostic_snapshot(student, subject_id: Optional[int]) -> Dict[str, int]:
    if subject_id:
        required_skills = (
            QuestionStep.objects.filter(question__lesson__topic__subject_id=subject_id)
            .values_list("skill_id", flat=True)
            .distinct()
            .count()
        )
        required_skills = min(12, max(6, required_skills)) if required_skills else 8
    else:
        required_skills = 8
    attempted_skills = (
        StudentSkillState.objects.filter(student=student, attempts__gte=3)
        .values_list("skill_id", flat=True)
        .distinct()
        .count()
    )
    return {
        "attempted_skills": attempted_skills,
        "required_skills": required_skills,
    }


def build_learning_mission(student, subject_id: Optional[int] = None) -> Dict[str, Any]:
    setting = (
        StudentExamSettings.objects.filter(student=student, subject_id=subject_id).first()
        if subject_id
        else StudentExamSettings.objects.filter(student=student).select_related("subject").first()
    )
    if setting and not subject_id:
        subject_id = setting.subject_id

    predicted_grade = _estimate_predicted_grade(student, subject_id)
    target_grade = setting.target_grade if setting else 5
    gap = max(0, target_grade - predicted_grade)
    risk_level = _risk_from_gap(gap)

    weak_states = list(
        StudentSkillState.objects.filter(
            student=student,
            attempts__gte=3,
            status__in=["NEW", "LEARNING", "IMPROVING", "AT_RISK"],
        )
        .select_related("skill")
        .order_by("rolling_accuracy")[:3]
    )
    weak_skill_codes = [s.skill.code for s in weak_states]

    recent_attempts = list(student.quiz_attempts.order_by("-attempted_at")[:12])
    total_recent = len(recent_attempts)
    recent_correct = sum(1 for a in recent_attempts if a.is_correct) if total_recent else 0
    recent_acc = (recent_correct / total_recent) if total_recent else 0.0
    last_attempt = recent_attempts[0] if recent_attempts else None
    days_since = None
    if last_attempt and last_attempt.attempted_at:
        days_since = (timezone.now() - last_attempt.attempted_at).days

    diagnostic_progress = _diagnostic_snapshot(student, subject_id)
    diagnostic_required = diagnostic_progress["attempted_skills"] < 5

    task_type = "diagnostic"
    reason = "Start a short diagnostic to map your strongest and weakest skills."
    parent_reason = "The student needs an initial baseline before grade-risk can be reliably projected."
    cta_url = f"/practice/{subject_id}/" if subject_id else "/subjects/"

    if not diagnostic_required:
        if days_since is not None and days_since >= 12 and recent_acc >= 0.85:
            task_type = "flashcards"
            reason = "You are strong but inactive recently. Run a maintenance refresh to prevent decay."
            parent_reason = "Recent inactivity after strong performance suggests maintenance practice."
            cta_url = "/flashcards/"
        elif recent_acc < 0.55 or risk_level == "at_risk":
            task_type = "drill"
            reason = "Accuracy is below your target path. Focused drill is the fastest recovery route."
            parent_reason = "Current performance sits below target-grade trajectory and needs targeted remediation."
        elif recent_acc >= 0.85 and risk_level == "on_track":
            task_type = "exam_sim"
            reason = "You are stable on core skills. Timed exam-style questions will build exam fluency."
            parent_reason = "Student is on track; exam simulation is appropriate for readiness and speed."
            cta_url = "/mock-tests/"
        else:
            task_type = "mixed_practice"
            reason = "You are improving. Mixed practice will stabilize performance across topics."
            parent_reason = "Student performance is mid-band; interleaved practice reduces regression risk."

    if not subject_id:
        first_subject_question = (
            Question.objects.filter(is_active=True)
            .values_list("lesson__topic__subject_id", flat=True)
            .first()
        )
        if first_subject_question:
            subject_id = first_subject_question
            cta_url = f"/practice/{subject_id}/"

    context = MissionContext(
        task_type=task_type,
        subject_id=subject_id,
        topic_id=None,
        skill_codes=weak_skill_codes,
        reason=reason,
        parent_reason=parent_reason,
        risk_level=risk_level,
        target_grade_gap=gap,
        cta_url=cta_url,
        diagnostic_required=diagnostic_required,
        diagnostic_progress=diagnostic_progress,
    )

    now = timezone.now()
    week_start = now - timedelta(days=7)
    sessions_last_week = student.study_sessions.filter(started_at__gte=week_start).count()

    payload = context.to_dict()
    payload.update(
        {
            "predicted_grade": predicted_grade,
            "target_grade": target_grade,
            "sessions_last_week": sessions_last_week,
        }
    )
    return payload
