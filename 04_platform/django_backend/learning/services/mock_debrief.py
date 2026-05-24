from collections import defaultdict

from dashboard.models import MockExamAttemptAnswer
from learning.models import MistakeBankItem


def build_mock_debrief(attempt):
    """Build a post-exam repair plan from marks lost and topic performance."""
    answers = (
        MockExamAttemptAnswer.objects.filter(attempt=attempt)
        .select_related("question", "question__lesson__topic", "question__lesson__topic__subject")
    )
    topic_rows = defaultdict(lambda: {"marks": 0, "available": 0, "wrong_questions": 0})
    total_lost = 0
    correct_count = 0
    answered_count = 0

    for answer in answers:
        q = answer.question
        topic = q.lesson.topic
        available = int(getattr(q, "marks_available", 1) or 1)
        achieved = int(answer.marks_achieved or 0)
        lost = max(0, available - achieved)
        topic_rows[topic]["marks"] += achieved
        topic_rows[topic]["available"] += available
        if lost:
            topic_rows[topic]["wrong_questions"] += 1
            total_lost += lost
        else:
            correct_count += 1
        answered_count += 1

    topic_breakdown = []
    for topic, row in topic_rows.items():
        available = row["available"] or 1
        pct = round(100.0 * row["marks"] / available, 1)
        topic_breakdown.append(
            {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "subject_name": topic.subject.display_name,
                "marks": row["marks"],
                "available": row["available"],
                "percentage": pct,
                "wrong_questions": row["wrong_questions"],
                "repair_url": f"/practice/topic/{topic.id}/",
            }
        )
    topic_breakdown.sort(key=lambda row: (row["percentage"], -row["wrong_questions"]))

    weakest_topics = topic_breakdown[:3]
    predicted_grade = attempt.predicted_grade or 1
    target_gap_text = ""
    try:
        setting = attempt.student.learning_exam_settings.filter(subject=attempt.mock_exam.subject).first()
        if setting:
            gap = setting.target_grade - predicted_grade
            if gap <= 0:
                target_gap_text = f"You are currently at or above your Grade {setting.target_grade} target on this mock."
            else:
                target_gap_text = f"You are about {gap} grade band(s) below your Grade {setting.target_grade} target on this mock."
    except Exception:
        target_gap_text = ""

    repair_steps = []
    for row in weakest_topics:
        repair_steps.append(
            {
                "label": f"Repair {row['topic_name']}",
                "reason": f"{row['marks']}/{row['available']} marks in this topic.",
                "url": row["repair_url"],
            }
        )
    active_mistakes = MistakeBankItem.objects.filter(
        student=attempt.student,
        topic__subject=attempt.mock_exam.subject,
        status__in=["active", "retrying"],
    ).count()
    if active_mistakes:
        repair_steps.append(
            {
                "label": "Clear mistake-bank items",
                "reason": f"{active_mistakes} active item(s) are still blocking exam readiness.",
                "url": "/mistakes/",
            }
        )

    if not repair_steps:
        repair_steps.append(
            {
                "label": "Try another timed paper",
                "reason": "No major weak topic emerged from this attempt.",
                "url": "/mock-tests/",
            }
        )

    percentage = attempt.percentage_score or 0
    if percentage >= 75:
        summary = "Strong timed performance. Focus on small mark-loss patterns and exam fluency."
    elif percentage >= 60:
        summary = "Solid base. A few topic repairs could move this into a higher grade band."
    elif percentage >= 40:
        summary = "Useful diagnostic mock. The priority is targeted repair before another full paper."
    else:
        summary = "This mock exposed foundations to rebuild. Use short repair sessions before retesting."

    return {
        "attempt_id": attempt.id,
        "mock_title": attempt.mock_exam.title,
        "subject_name": attempt.mock_exam.subject.display_name,
        "percentage_score": percentage,
        "predicted_grade": predicted_grade,
        "marks_achieved": attempt.marks_achieved or 0,
        "marks_available": attempt.total_marks_available or 0,
        "answered_questions": answered_count,
        "correct_questions": correct_count,
        "marks_lost": total_lost,
        "summary": summary,
        "target_gap": target_gap_text,
        "weakest_topics": weakest_topics,
        "repair_steps": repair_steps[:4],
    }
