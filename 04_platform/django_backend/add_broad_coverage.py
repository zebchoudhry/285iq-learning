import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import Subject, Topic, Lesson, Question, QuizAttempt
from users.models import Student

student = Student.objects.get(id=7)
maths = Subject.objects.get(name='mathematics')

# Get ALL topics and lessons
all_topics = list(Topic.objects.filter(subject=maths))
print(f"\nTotal maths topics: {len(all_topics)}")

# Get questions from MANY different lessons
all_lessons = list(Lesson.objects.filter(topic__subject=maths))
print(f"Total maths lessons: {len(all_lessons)}")

# Get questions from diverse lessons
questions_by_lesson = {}
for lesson in all_lessons[:100]:  # Use first 100 lessons
    qs = list(Question.objects.filter(lesson=lesson)[:2])  # 2 questions per lesson
    if qs:
        questions_by_lesson[lesson.id] = qs

all_questions = [q for qs in questions_by_lesson.values() for q in qs]
print(f"Questions from {len(questions_by_lesson)} different lessons: {len(all_questions)}")

# Delete old attempts
print(f"\nDeleting old attempts...")
QuizAttempt.objects.filter(student=student).delete()

# Create attempts across MANY topics
print(f"Creating attempts with broad coverage...\n")

for week in range(8):
    days_ago_start = (7 - week) * 7
    questions_this_week = 15 + (week * 3)
    base_accuracy = 0.50 + (week * 0.03)
    
    for q in range(questions_this_week):
        days_ago = days_ago_start + random.randint(0, 6)
        question = random.choice(all_questions)
        is_correct = random.random() < base_accuracy
        
        QuizAttempt.objects.create(
            student=student,
            question=question,
            is_correct=is_correct,
            error_type='none' if is_correct else 'conceptual',
            attempted_at=datetime.now() - timedelta(days=days_ago)
        )
    
    print(f"Week {week+1}: {questions_this_week} questions at {base_accuracy*100:.0f}%")

# Check coverage
from decision_engine.v1_0.decision_engine_v1 import calculate_coverage_breadth
coverage = calculate_coverage_breadth(student.id, maths.id)

total = QuizAttempt.objects.filter(student=student).count()
print(f"\n✅ Created {total} attempts")
print(f"✅ Coverage: {coverage*100:.0f}%")
print(f"\n🎯 Refresh dashboard - should show Grade 5-6 now!")