"""
SIMPLIFIED QUESTION GENERATOR
Fixed Django import issues
"""

import os
import sys

# Get the correct Django backend path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')

# Initialize Django
import django
django.setup()

# Now import models
from learning.models import Subject, Topic, Lesson, Question
import random

print("\n" + "="*70)
print("🎓 GCSE MATHS QUESTION GENERATOR")
print("="*70)

# Get or create Mathematics
print("\n📚 Setting up Mathematics subject...")
maths, created = Subject.objects.get_or_create(
    name='mathematics',
    defaults={'display_name': 'GCSE Mathematics'}
)

if created:
    print("   ✅ Created Mathematics subject")
else:
    print(f"   ✅ Using existing Mathematics subject (ID: {maths.id})")

# Simple structure - generate 100 questions to test
print("\n🎯 Generating 100 test questions...")

# Create one topic
topic, _ = Topic.objects.get_or_create(
    subject=maths,
    name='Algebra',
    defaults={'order': 1, 'is_active': True}
)

# Create one lesson
lesson, _ = Lesson.objects.get_or_create(
    topic=topic,
    title='Linear Equations',
    defaults={
        'content': 'Practice solving linear equations',
        'estimated_duration': 60,
        'order': 1
    }
)

# Generate 100 questions
created_count = 0

for i in range(100):
    a = random.randint(2, 9)
    b = random.randint(-20, 20)
    c = random.randint(-50, 50)
    
    question_text = f"Solve: {a}x + {b} = {c}"
    answer = f"x = {(c - b) / a:.2f}"
    
    Question.objects.create(
        lesson=lesson,
        question_text=question_text,
        correct_answer=answer,
        question_type='short_answer',
        difficulty_level=random.choice([2, 3, 4]),
        marks_available=random.choice([1, 2, 3]),
        explanation='Rearrange to isolate x, then divide.',
        marking_scheme='1 mark for method, remaining for correct answer',
        exam_board='aqa'
    )
    
    created_count += 1
    
    if (i + 1) % 20 == 0:
        print(f"   Created {i + 1} questions...")

print(f"\n✅ Created {created_count} new questions")

# Get totals
total_questions = Question.objects.count()
maths_questions = Question.objects.filter(lesson__topic__subject=maths).count()

print(f"\n📊 Database Summary:")
print(f"   Total questions: {total_questions}")
print(f"   Maths questions: {maths_questions}")
print(f"   Topics: {Topic.objects.filter(subject=maths).count()}")
print(f"   Lessons: {Lesson.objects.filter(topic__subject=maths).count()}")

print("\n" + "="*70)
print("✅ Generation complete!")
print("="*70)
print("\n🎯 Next: Test Decision Engine with this content")
print()
