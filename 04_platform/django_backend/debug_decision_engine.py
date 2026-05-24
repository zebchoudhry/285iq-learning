import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from django.utils import timezone
from learning.models import Subject, QuizAttempt, StudentExamSettings
from users.models import Student
from decision_engine.v1_0.decision_engine_v1 import evaluate_student_subject
from decision_engine.v1_0.core import OutlookTier

student_id = 7
student = Student.objects.get(id=student_id)

# Get maths
maths = Subject.objects.get(name='"mathematics"'.strip('"'))
settings = StudentExamSettings.objects.get(student=student, subject=maths)

print("\n" + "="*60)
print("DEBUG DECISION ENGINE")
print("="*60)

# Check quiz attempts
total_attempts = QuizAttempt.objects.filter(student=student).count()
maths_attempts = QuizAttempt.objects.filter(
    student=student,
    question__lesson__topic__subject=maths
).count()

print(f"\nQuiz Attempts:")
print(f"  Total attempts: {total_attempts}")
print(f"  Maths attempts: {maths_attempts}")

# Check recent attempts (timezone-aware)
now = timezone.now()
recent_cutoff = now - timedelta(days=30)
recent_attempts = QuizAttempt.objects.filter(
    student=student,
    question__lesson__topic__subject=maths,
    attempted_at__gte=recent_cutoff
).count()

print(f"  Recent last 30 days: {recent_attempts}")

# Show some samples
samples = QuizAttempt.objects.filter(
    student=student,
    question__lesson__topic__subject=maths
)[:5]

print(f"\nSample Attempts:")
for attempt in samples:
    correct = "YES" if attempt.is_correct else "NO"
    print(f"  - {attempt.attempted_at.date()} | Correct: {correct} | Q: {attempt.question.id}")

# Call decision engine
print(f"\nCalling Decision Engine...")
print(f"  Student ID: {student_id}")
print(f"  Subject ID: {maths.id}")
print(f"  Exam Date: {settings.exam_date}")
print(f"  Target Grade: {settings.target_grade}")

try:
    previous_tier = None
    if settings.last_outlook_tier:
        try:
            previous_tier = OutlookTier(settings.last_outlook_tier)
        except Exception:
            previous_tier = None

    result = evaluate_student_subject(
        student_id=student_id,
        subject_id=maths.id,
        exam_date=settings.exam_date,
        target_grade=settings.target_grade,
        previous_tier=previous_tier
    )
    
    print(f"\nDecision Engine Result:")
    print(f"  Tier: {result['tier']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Attainment Band: {result['attainment_band']}")
    print(f"  Trend: {result['trend']}")
    print(f"  Weeks Remaining: {result['weeks_remaining']}")
    print(f"  Activity per Week: {result['activity_per_week']}")
    print(f"  Coverage: {result['coverage_breadth']}")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
