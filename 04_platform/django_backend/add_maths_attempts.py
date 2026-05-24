import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import Subject, Question, QuizAttempt
from users.models import Student

student = Student.objects.get(id=7)

# Get MATHEMATICS subject specifically
maths = Subject.objects.get(name='mathematics')

# Get questions from MATHS lessons only
maths_questions = list(Question.objects.filter(
    lesson__topic__subject=maths
)[:50])

print(f"\nFound {len(maths_questions)} maths questions")
print(f"Adding 80 quiz attempts for {student.username} in MATHEMATICS\n")

# Add 80 attempts over last 4 weeks with improving performance
for i in range(80):
    question = random.choice(maths_questions)
    days_ago = random.randint(0, 28)
    
    # Performance improves: 55% → 85%
    accuracy = 0.55 + (i * 0.004)
    is_correct = random.random() < accuracy
    
    QuizAttempt.objects.create(
        student=student,
        question=question,
        is_correct=is_correct,
        error_type='none' if is_correct else 'conceptual',
        attempted_at=datetime.now() - timedelta(days=days_ago),
        time_spent_ms=random.randint(30000, 180000)  # 30s-3min
    )
    
    if (i + 1) % 20 == 0:
        print(f"  Created {i + 1} attempts...")

print(f"\n✅ Done! Created 80 MATHS quiz attempts")
print(f"Total attempts in database: {QuizAttempt.objects.count()}")
print(f"\n🎯 Now refresh: http://127.0.0.1:8000/api/parent/dashboard/7/")