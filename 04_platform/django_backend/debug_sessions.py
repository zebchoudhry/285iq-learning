import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import Subject, StudySession, QuizAttempt
from users.models import Student

student = Student.objects.get(id=7)
maths = Subject.objects.get(name='mathematics')

print("\n" + "="*60)
print("DEBUG: StudySessions and QuizAttempts")
print("="*60)

# Check StudySessions
total_sessions = StudySession.objects.filter(
    student=student,
    subject=maths
).count()

recent_sessions = StudySession.objects.filter(
    student=student,
    subject=maths,
    started_at__gte=date.today() - timedelta(days=28)
).count()

print(f"\nStudySessions:")
print(f"  Total: {total_sessions}")
print(f"  Last 28 days: {recent_sessions}")
print(f"  Per week (avg): {recent_sessions / 4:.1f}")

# Show sample sessions
samples = StudySession.objects.filter(
    student=student,
    subject=maths
).order_by('-started_at')[:5]

print(f"\nSample Sessions:")
for session in samples:
    print(f"  {session.started_at.date()} | Duration: {session.duration_seconds}s | Qs: {session.questions_correct}/{session.questions_attempted}")

# Check QuizAttempts
quiz_count = QuizAttempt.objects.filter(
    student=student,
    question__lesson__topic__subject=maths
).count()

print(f"\nQuizAttempts: {quiz_count}")

# Now check what decision engine calculates
print(f"\n" + "="*60)
print("Testing Decision Engine Functions Directly...")
print("="*60)

from decision_engine.v1_0.decision_engine_v1 import count_recent_sessions, build_weekly_summaries

# Test count_recent_sessions
try:
    session_count = count_recent_sessions(student.id, maths.id)
    print(f"\ncount_recent_sessions() returned: {session_count}")
except Exception as e:
    print(f"\nERROR in count_recent_sessions(): {e}")

# Test build_weekly_summaries
try:
    summaries = build_weekly_summaries(student.id, maths.id)
    print(f"\nbuild_weekly_summaries() returned {len(summaries)} weeks:")
    for summary in summaries[:3]:
        print(f"  Week ending {summary.week_ending}: {summary.questions_correct}/{summary.questions_total} correct")
except Exception as e:
    print(f"\nERROR in build_weekly_summaries(): {e}")

print("\n" + "="*60)