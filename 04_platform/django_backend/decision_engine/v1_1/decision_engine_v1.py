"""
Decision Engine v1.1 - Django Adapter (FIXED)
Connects Django ORM to pure decision logic.
"""

from datetime import date, timedelta
from typing import Dict, Any, List
from collections import defaultdict

from decision_engine.v1_1.core import (
    WeeklyPerformanceSummary,
    calculate_weeks_remaining,
    calculate_attainment_band_from_skill,
    calculate_performance_trend,
    assign_outlook_tier,
    OutlookTier,
)

from learning.models import QuizAttempt, Topic, StudySession, StudentTopicSkill


def build_weekly_summaries(
    student_id: int,
    subject_id: int,
    weeks: int = 8
) -> List[WeeklyPerformanceSummary]:
    """
    Aggregate quiz attempts into weekly performance summaries.
    """
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)
    
    # Get all attempts in date range
    attempts = QuizAttempt.objects.filter(
        student_id=student_id,
        question__lesson__topic__subject_id=subject_id,
        attempted_at__date__gte=start_date,
        attempted_at__date__lte=end_date
    ).select_related('question__lesson__topic')
    
    # Group by week
    weekly_data = defaultdict(lambda: {
        'correct': 0,
        'total': 0,
        'topics': set(),
        'difficulties': []
    })
    
    for attempt in attempts:
        # Calculate week ending date (Sunday)
        attempt_date = attempt.attempted_at.date()
        days_until_sunday = (6 - attempt_date.weekday()) % 7
        week_ending = attempt_date + timedelta(days=days_until_sunday)
        
        if attempt.is_correct:
            weekly_data[week_ending]['correct'] += 1
        weekly_data[week_ending]['total'] += 1
        weekly_data[week_ending]['topics'].add(attempt.question.lesson.topic_id)
        weekly_data[week_ending]['difficulties'].append(attempt.question.difficulty_level)
    
    # Build WeeklyPerformanceSummary objects
    summaries = []
    for week_ending in sorted(weekly_data.keys()):
        data = weekly_data[week_ending]
        
        if data['total'] == 0:
            continue
        
        accuracy = data['correct'] / data['total']
        avg_difficulty = sum(data['difficulties']) / len(data['difficulties']) if data['difficulties'] else 2.0
        
        summaries.append(WeeklyPerformanceSummary(
            week_ending=week_ending,
            average_accuracy=accuracy,
            questions_attempted=data['total'],
            topics_accessed=len(data['topics']),
            difficulty_distribution=avg_difficulty / 4.0
        ))
    
    return summaries


def calculate_coverage_breadth(student_id: int, subject_id: int) -> float:
    """
    Calculate what fraction of the subject's topics have been attempted.
    """
    total_topics = Topic.objects.filter(
        subject_id=subject_id,
        is_active=True
    ).count()
    
    if total_topics == 0:
        return 0.0
    
    attempted_topics = QuizAttempt.objects.filter(
        student_id=student_id,
        question__lesson__topic__subject_id=subject_id
    ).values('question__lesson__topic_id').distinct().count()
    
    return min(1.0, attempted_topics / total_topics)


def count_recent_sessions(student_id: int, subject_id: int, weeks: int = 4) -> int:
    """
    Count study sessions in recent weeks.
    FIXED: Now properly counts StudySession objects.
    """
    start_date = date.today() - timedelta(weeks=weeks)

    # Try to use StudySession model if available
    try:
        session_count = StudySession.objects.filter(
            student_id=student_id,
            subject_id=subject_id,
            started_at__date__gte=start_date
        ).count()
        
        # Return sessions per week
        return round(session_count / weeks) if weeks > 0 else 0
    
    except Exception:
        # Fallback: estimate from quiz attempts by counting unique days
        session_days = QuizAttempt.objects.filter(
            student_id=student_id,
            question__lesson__topic__subject_id=subject_id,
            attempted_at__date__gte=start_date
        ).values('attempted_at__date').distinct().count()
        
        # Return sessions per week (assume 1 session per active day)
        return round(session_days / weeks) if weeks > 0 else 0


def evaluate_student_subject(
    student_id: int,
    subject_id: int,
    exam_date: date,
    target_grade: int = 5,
    previous_tier: OutlookTier = None
) -> Dict[str, Any]:
    """
    Evaluate a student's outlook for a specific subject.
    
    This is the main entry point for the decision engine.
    """
    # Build weekly performance summaries
    weekly = build_weekly_summaries(student_id, subject_id, weeks=8)
    
    # Calculate coverage
    coverage = calculate_coverage_breadth(student_id, subject_id)
    
    # Calculate metrics
    weeks_remaining = calculate_weeks_remaining(exam_date, date.today())

    skills = list(
        StudentTopicSkill.objects.filter(
            student_id=student_id,
            topic__subject_id=subject_id,
        )
    )
    total_attempts = sum(s.attempt_count for s in skills)
    if not skills or total_attempts == 0:
        median_skill = 1500.0
        rating_confidence = 0.0
    else:
        ratings = sorted(s.skill_rating for s in skills)
        mid = len(ratings) // 2
        median_skill = ratings[mid] if len(ratings) % 2 else (ratings[mid - 1] + ratings[mid]) / 2
        rating_confidence = min(1.0, total_attempts / 200.0)

    band, lower, upper = calculate_attainment_band_from_skill(
        median_skill_rating=median_skill,
        coverage_breadth=coverage,
        rating_confidence=rating_confidence,
        total_attempts=total_attempts,
    )

    trend = calculate_performance_trend(weekly)
    activity = count_recent_sessions(student_id, subject_id)
    
    # Assign tier
    tier, reason = assign_outlook_tier(
        attainment_band=band,
        target_grade=target_grade,
        trend=trend,
        activity_per_week=activity,
        weeks_remaining=weeks_remaining,
        previous_tier=previous_tier,
        hysteresis=None,
    )
    
    return {
        "tier": tier.value,
        "reason": reason,
        "attainment_band": band,
        "trend": trend.value,
        "weeks_remaining": weeks_remaining,
        "coverage_breadth": coverage,
        "activity_per_week": activity,
        "predicted_grade_range": (lower, upper),
        "rating_confidence": round(rating_confidence, 2),
    }
