from datetime import date, timedelta
from enum import Enum
from typing import Dict, List


class StudyModeType(Enum):
    FOUNDATION = "foundation"
    CONSOLIDATION = "consolidation"
    INTENSIVE = "intensive"
    CRAM = "cram"
    EXAM_WEEK = "exam_week"
    POST_EXAM = "post_exam"


def calculate_study_mode(exam_date: date, today: date = None) -> Dict:
    """
    Determine study mode based on days until exam
    
    Args:
        exam_date: Date of the exam
        today: Current date (defaults to today)
        
    Returns:
        {
            'mode': StudyModeType,
            'days_until_exam': int,
            'sessions_per_week': int,
            'minutes_per_session': int,
            'new_content_ratio': float (0.0-1.0),
            'focus': str,
            'description': str
        }
    """
    if today is None:
        today = date.today()
    
    days_until = (exam_date - today).days
    
    # POST EXAM (exam has passed)
    if days_until < 0:
        return {
            'mode': StudyModeType.POST_EXAM,
            'days_until_exam': days_until,
            'sessions_per_week': 0,
            'minutes_per_session': 0,
            'new_content_ratio': 0.0,
            'focus': 'rest',
            'description': 'Exam complete! Take a break. 🎉'
        }
    
    # EXAM WEEK (0-7 days) - CRAM MODE ACTIVATED
    elif days_until <= 7:
        return {
            'mode': StudyModeType.EXAM_WEEK,
            'days_until_exam': days_until,
            'sessions_per_week': 7,  # Every day
            'minutes_per_session': 20,  # Short, focused bursts
            'new_content_ratio': 0.0,  # ZERO new content
            'focus': 'revision_only',
            'description': f'🔥 CRAM MODE: {days_until} days until exam!'
        }
    
    # CRAM MODE (8-14 days)
    elif days_until <= 14:
        return {
            'mode': StudyModeType.CRAM,
            'days_until_exam': days_until,
            'sessions_per_week': 6,
            'minutes_per_session': 30,
            'new_content_ratio': 0.1,  # Minimal new content
            'focus': 'weak_topics',
            'description': f'{days_until} days left - focus on weak areas'
        }
    
    # INTENSIVE (15-42 days / 2-6 weeks)
    elif days_until <= 42:
        weeks = days_until // 7
        return {
            'mode': StudyModeType.INTENSIVE,
            'days_until_exam': days_until,
            'sessions_per_week': 5,
            'minutes_per_session': 35,
            'new_content_ratio': 0.3,  # Some new content
            'focus': 'exam_practice',
            'description': f'{weeks} weeks left - intensive revision'
        }
    
    # CONSOLIDATION (43-84 days / 6-12 weeks)
    elif days_until <= 84:
        weeks = days_until // 7
        return {
            'mode': StudyModeType.CONSOLIDATION,
            'days_until_exam': days_until,
            'sessions_per_week': 4,
            'minutes_per_session': 40,
            'new_content_ratio': 0.5,  # Balanced
            'focus': 'consolidation',
            'description': f'{weeks} weeks left - consolidate knowledge'
        }
    
    # FOUNDATION (85+ days / 12+ weeks)
    else:
        weeks = days_until // 7
        return {
            'mode': StudyModeType.FOUNDATION,
            'days_until_exam': days_until,
            'sessions_per_week': 4,
            'minutes_per_session': 45,
            'new_content_ratio': 0.7,  # Mostly new content
            'focus': 'curriculum_coverage',
            'description': f'{weeks} weeks left - build strong foundation'
        }


def generate_cram_schedule(exam_date: date, weak_topics: List[str]) -> List[Dict]:
    """
    Generate daily cram schedule for last 7 days before exam
    
    Args:
        exam_date: Date of exam
        weak_topics: List of topic names student struggles with
        
    Returns:
        List of daily session plans
    """
    today = date.today()
    days_until = (exam_date - today).days
    
    if days_until > 7:
        return []  # Not in cram mode yet
    
    schedule = []
    
    for day_offset in range(max(0, 7 - days_until), 7):
        session_date = exam_date - timedelta(days=7 - day_offset)
        
        if day_offset == 0:  # 7 days out
            schedule.append({
                'date': session_date.isoformat(),
                'day_label': '7 days before',
                'sessions': [
                    {'time': 'morning', 'topic': weak_topics[0] if weak_topics else 'revision', 'duration': 20, 'type': 'revision'},
                    {'time': 'afternoon', 'topic': weak_topics[1] if len(weak_topics) > 1 else 'revision', 'duration': 20, 'type': 'revision'},
                    {'time': 'evening', 'topic': weak_topics[2] if len(weak_topics) > 2 else 'revision', 'duration': 20, 'type': 'revision'},
                ]
            })
        
        elif day_offset <= 4:  # 6-3 days out
            schedule.append({
                'date': session_date.isoformat(),
                'day_label': f'{7 - day_offset} days before',
                'sessions': [
                    {'time': 'morning', 'topic': 'Past Paper', 'duration': 15, 'type': 'past_paper'},
                    {'time': 'afternoon', 'topic': 'Review mistakes', 'duration': 20, 'type': 'review'},
                    {'time': 'evening', 'topic': weak_topics[day_offset % len(weak_topics)] if weak_topics else 'practice', 'duration': 15, 'type': 'quick_drill'},
                ]
            })
        
        elif day_offset == 5:  # 2 days out
            schedule.append({
                'date': session_date.isoformat(),
                'day_label': '2 days before',
                'sessions': [
                    {'time': 'morning', 'topic': 'Full Past Paper', 'duration': 90, 'type': 'full_past_paper'},
                    {'time': 'afternoon', 'topic': 'Review only', 'duration': 30, 'type': 'review'},
                ]
            })
        
        elif day_offset == 6:  # 1 day out
            schedule.append({
                'date': session_date.isoformat(),
                'day_label': '1 day before',
                'sessions': [
                    {'time': 'morning', 'topic': 'Formula flashcards', 'duration': 15, 'type': 'memorization'},
                    {'time': 'afternoon', 'topic': 'Easy confidence boosters', 'duration': 20, 'type': 'confidence'},
                ]
            })
    
    return schedule