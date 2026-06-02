"""
Revision timetable builder for GCSE students.
"""
import logging
from datetime import date, timedelta
from typing import List

logger = logging.getLogger(__name__)


def build_revision_timetable(student, days_ahead: int = 42) -> List[dict]:
    """
    Returns a list of daily revision slots for the next `days_ahead` days.

    Each slot:
        {"date": "2026-06-03", "subject_id": 1, "subject_name": "...",
         "topic_id": 5, "topic_name": "...", "session_type": "practice"|"review"|"mock",
         "reason": "Weak area", "priority": "high"|"medium"|"low"}

    Algorithm:
    1. Get all StudentExamSettings for student
    2. Sort subjects by weeks_remaining (most urgent first)
    3. Get weak topics from StudentTopicPerformance (success_rate < 60%)
    4. Distribute sessions across days: 1-2 sessions/day, rotating subjects,
       prioritising weak topics in urgent subjects
    5. Reserve the 3 days before each exam for mock/review only
    """
    from learning.models import StudentExamSettings, Topic
    from users.models import StudentTopicPerformance

    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    # 1. Get exam settings, sorted by urgency (soonest exam first)
    settings_qs = (
        StudentExamSettings.objects
        .filter(student=student, exam_date__gte=today)
        .select_related('subject')
        .order_by('exam_date')
    )
    settings_list = list(settings_qs)

    if not settings_list:
        logger.debug("build_revision_timetable: no exam settings for student %s", student.pk)
        return []

    # Build map of subject_id -> (settings, weeks_remaining)
    subject_info = {}
    for s in settings_list:
        days_remaining = (s.exam_date - today).days
        weeks_remaining = max(0, days_remaining // 7)
        subject_info[s.subject_id] = {
            "settings": s,
            "subject_name": s.subject.display_name,
            "exam_date": s.exam_date,
            "target_grade": s.target_grade,
            "weeks_remaining": weeks_remaining,
        }

    # 2. Sort subjects by urgency (fewest weeks first)
    sorted_subjects = sorted(subject_info.items(), key=lambda x: x[1]["weeks_remaining"])

    # 3. Get weak topics per subject (success_rate < 60%)
    subject_weak_topics: dict = {}
    for subj_id, info in sorted_subjects:
        perfs = list(
            StudentTopicPerformance.objects
            .filter(student=student, topic__subject_id=subj_id, questions_attempted__gte=3)
            .select_related("topic")
        )
        weak = []
        strong = []
        for p in perfs:
            rate = (p.questions_correct / p.questions_attempted) if p.questions_attempted else 1.0
            if rate < 0.6:
                weak.append(p.topic)
            else:
                strong.append(p.topic)

        # Fall back to all topics if no performance data
        if not weak and not strong:
            all_topics = list(Topic.objects.filter(subject_id=subj_id, is_active=True))
            weak = all_topics

        subject_weak_topics[subj_id] = {"weak": weak, "strong": strong}

    # 4. Build exam-day blackout sets (3 days before each exam → mock/review only)
    mock_days: dict = {}  # date -> subject_id
    for subj_id, info in subject_info.items():
        exam_dt = info["exam_date"]
        for offset in range(1, 4):
            day = exam_dt - timedelta(days=offset)
            if today <= day <= end_date:
                mock_days[day] = subj_id

    # 5. Distribute sessions across days
    timetable: List[dict] = []
    subject_cycle = [sid for sid, _ in sorted_subjects]
    # We need a cycling pointer per subject for topic rotation
    topic_pointers: dict = {sid: 0 for sid in subject_cycle}

    subj_cycle_idx = 0
    current_day = today + timedelta(days=1)  # start tomorrow

    while current_day <= end_date:
        sessions_today = 0
        max_sessions = 2 if current_day.weekday() in (5, 6) else 1  # 2 on weekends

        # Check if this day is a mock/review blackout for a subject
        if current_day in mock_days:
            subj_id = mock_days[current_day]
            info = subject_info[subj_id]
            timetable.append({
                "date": current_day.isoformat(),
                "subject_id": subj_id,
                "subject_name": info["subject_name"],
                "topic_id": None,
                "topic_name": "Full exam paper",
                "session_type": "mock",
                "reason": f"Exam in {(info['exam_date'] - current_day).days} day(s)",
                "priority": "high",
            })
            current_day += timedelta(days=1)
            continue

        while sessions_today < max_sessions and subj_cycle_idx < len(subject_cycle) * days_ahead:
            if not subject_cycle:
                break

            # Pick next subject in rotation
            subj_id = subject_cycle[subj_cycle_idx % len(subject_cycle)]
            subj_cycle_idx += 1
            info = subject_info[subj_id]
            topics_data = subject_weak_topics.get(subj_id, {"weak": [], "strong": []})

            # Choose topic
            weak_topics = topics_data["weak"]
            strong_topics = topics_data["strong"]

            if weak_topics:
                ptr = topic_pointers[subj_id]
                topic = weak_topics[ptr % len(weak_topics)]
                topic_pointers[subj_id] = ptr + 1
                session_type = "practice"
                reason = "Weak area"
                priority = "high" if info["weeks_remaining"] <= 4 else "medium"
            elif strong_topics:
                ptr = topic_pointers[subj_id]
                topic = strong_topics[ptr % len(strong_topics)]
                topic_pointers[subj_id] = ptr + 1
                session_type = "review"
                reason = "Consolidate knowledge"
                priority = "low"
            else:
                sessions_today += 1
                continue

            timetable.append({
                "date": current_day.isoformat(),
                "subject_id": subj_id,
                "subject_name": info["subject_name"],
                "topic_id": topic.id,
                "topic_name": topic.name,
                "session_type": session_type,
                "reason": reason,
                "priority": priority,
            })
            sessions_today += 1

        current_day += timedelta(days=1)

    logger.debug(
        "build_revision_timetable: generated %d slots for student %s over %d days",
        len(timetable), student.pk, days_ahead,
    )
    return timetable
