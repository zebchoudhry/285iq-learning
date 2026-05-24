import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from learning.models import Subject, Lesson, Question

# Get maths
maths = Subject.objects.get(name='mathematics')

# Get first 10 lessons
lessons = Lesson.objects.filter(topic__subject=maths)  # ALL lessons

print(f"\nFound {lessons.count()} lessons\n")

# Create 5 questions per lesson
total = 0

for lesson in lessons:
    for i in range(5):
        a = random.randint(2, 9)
        b = random.randint(-20, 20)
        c = random.randint(-50, 50)
        answer = round((c - b) / a, 2)
        
        Question.objects.create(
            lesson=lesson,
            question_text=f"Solve: {a}x + {b} = {c}",
            correct_answer=f"x = {answer}",
            question_type='short_answer',
            difficulty_level=2,
            marks_available=2,
            exam_board='aqa'
        )
        total += 1
    
    print(f"Created 5 questions for: {lesson.title}")

print(f"\nDone! Total questions created: {total}")
print(f"Total questions in database: {Question.objects.count()}")