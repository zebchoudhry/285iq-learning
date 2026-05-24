import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import Subject, Question, QuizAttempt
from users.models import Student

student = Student.objects.get(id=7)
maths = Subject.objects.get(name='mathematics')
questions = list(Question.objects.filter(lesson__topic__subject=maths)[:50])

print(f"\nDeleting old quiz attempts...")
QuizAttempt.objects.filter(student=student).delete()

print(f"Creating new quiz attempts spread over 8 weeks...\n")

# Create attempts over 8 weeks with improving trend
for week in range(8):
    days_ago_start = (7 - week) * 7  # Week 0 = 49-56 days ago, Week 7 = 0-7 days ago
    
    # Questions per week increases over time (10 → 40)
    questions_this_week = 10 + (week * 4)
    
    # Accuracy improves over time (50% → 75%)
    base_accuracy = 0.50 + (week * 0.03)
    
    for q in range(questions_this_week):
        days_ago = days_ago_start + random.randint(0, 6)
        question = random.choice(questions)
        
        is_correct = random.random() < base_accuracy
        
        QuizAttempt.objects.create(
            student=student,
            question=question,
            is_correct=is_correct,
            error_type='none' if is_correct else 'conceptual',
            attempted_at=datetime.now() - timedelta(days=days_ago)
        )
    
    accuracy_pct = base_accuracy * 100
    print(f"Week {week+1}: {questions_this_week} questions at {accuracy_pct:.0f}% accuracy")

total = QuizAttempt.objects.filter(student=student).count()
print(f"\n✅ Created {total} quiz attempts over 8 weeks")
print(f"\n🎯 Now refresh the dashboard!")