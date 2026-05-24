import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import Question, QuizAttempt
from users.models import Student

student = Student.objects.get(id=7)
questions = list(Question.objects.all()[:50])

print(f"\nAdding quiz attempts for {student.username}")
print(f"Using {len(questions)} questions\n")

# Add 60 attempts over last 4 weeks with improving performance
for i in range(60):
    question = random.choice(questions)
    days_ago = random.randint(0, 28)
    
    # Performance improves: 50% → 75%
    accuracy = 0.50 + (i * 0.004)
    is_correct = random.random() < accuracy
    
    QuizAttempt.objects.create(
        student=student,
        question=question,
        is_correct=is_correct,
        error_type='none' if is_correct else 'conceptual',
        attempted_at=datetime.now() - timedelta(days=days_ago)
    )

print(f"\n✅ Created 60 quiz attempts")
print(f"Total in database: {QuizAttempt.objects.count()}")
print(f"\n🎯 Now refresh the Parent Dashboard!")