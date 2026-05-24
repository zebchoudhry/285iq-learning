import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import StudySession, QuizAttempt
from datetime import date, timedelta
from collections import defaultdict

def count_recent_sessions_FIXED(student_id, subject_id, days=28):
    """Count study sessions in last N days"""
    cutoff = date.today() - timedelta(days=days)
    
    count = StudySession.objects.filter(
        student_id=student_id,
        subject_id=subject_id,
        started_at__gte=cutoff
    ).count()
    
    return count

def build_weekly_summaries_FIXED(student_id, subject_id):
    """Build weekly performance from QuizAttempts"""
    
    cutoff = date.today() - timedelta(days=90)
    
    attempts = QuizAttempt.objects.filter(
        student_id=student_id,
        question__lesson__topic__subject_id=subject_id,
        attempted_at__gte=cutoff
    ).order_by('attempted_at')
    
    # Group by week
    weekly_data = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    for attempt in attempts:
        # Get week ending (Sunday)
        days_to_sunday = (6 - attempt.attempted_at.weekday()) % 7
        week_end = (attempt.attempted_at + timedelta(days=days_to_sunday)).date()
        
        weekly_data[week_end]['total'] += 1
        if attempt.is_correct:
            weekly_data[week_end]['correct'] += 1
    
    summaries = []
    for week_end, data in sorted(weekly_data.items()):
        summaries.append({
            'week_ending': week_end,
            'questions_total': data['total'],
            'questions_correct': data['correct'],
            'accuracy': data['correct'] / data['total'] if data['total'] > 0 else 0
        })
    
    return summaries

# Test it
student_id = 7
subject_id = 1

print("\nTesting FIXED functions...")
print("="*60)

count = count_recent_sessions_FIXED(student_id, subject_id)
print(f"\ncount_recent_sessions: {count} sessions")
print(f"Per week: {count / 4:.1f}")

summaries = build_weekly_summaries_FIXED(student_id, subject_id)
print(f"\nbuild_weekly_summaries: {len(summaries)} weeks")
for s in summaries[:3]:
    acc = s['accuracy'] * 100
    print(f"  Week {s['week_ending']}: {s['questions_correct']}/{s['questions_total']} = {acc:.0f}%")

# Calculate grade
if summaries:
    recent_accuracy = sum(s['accuracy'] for s in summaries[-4:]) / min(len(summaries), 4)
    
    if recent_accuracy >= 0.85:
        grade = 8
    elif recent_accuracy >= 0.75:
        grade = 7
    elif recent_accuracy >= 0.65:
        grade = 6
    elif recent_accuracy >= 0.55:
        grade = 5
    elif recent_accuracy >= 0.45:
        grade = 4
    else:
        grade = 3
    
    print(f"\nCalculated Attainment: Grade {grade}")
    print(f"Based on {recent_accuracy*100:.0f}% accuracy")
    print(f"Sessions per week: {count / 4:.1f}")
    print(f"\nThis should show STRETCH_ACHIEVABLE or ON_TRACK!")

print("\n" + "="*60)