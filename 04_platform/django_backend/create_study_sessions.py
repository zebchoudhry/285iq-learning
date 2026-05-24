import os
import django
import random
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studymate285.settings')
django.setup()

from django.utils import timezone

from learning.models import Subject, StudySession, Topic
from users.models import Student

student = Student.objects.get(id=7)
maths = Subject.objects.get(name='mathematics')

# Get some maths topics
topics = list(Topic.objects.filter(subject=maths)[:10])

print(f"\nCreating study sessions for {student.username}")
print(f"Subject: {maths.display_name}")
print(f"Topics: {len(topics)}\n")

# Create 30 study sessions over last 4 weeks
for i in range(30):
    days_ago = random.randint(0, 28)
    started = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 12))
    
    # Session duration: 15-45 minutes
    duration = random.randint(900, 2700)
    ended = started + timedelta(seconds=duration)
    
    # Questions attempted: 5-15
    questions_attempted = random.randint(5, 15)
    
    # Accuracy improves over time: 60% → 85%
    accuracy = 0.60 + (i * 0.008)
    questions_correct = int(questions_attempted * accuracy)
    
    StudySession.objects.create(
        student=student,
        subject=maths,
        topic=random.choice(topics) if topics else None,
        started_at=started,
        ended_at=ended,
        duration_seconds=duration,
        questions_attempted=questions_attempted,
        questions_correct=questions_correct
    )
    
    if (i + 1) % 10 == 0:
        print(f"  Created {i + 1} sessions...")

total_sessions = StudySession.objects.filter(student=student, subject=maths).count()

print(f"\nDone!")
print(f"Total study sessions: {total_sessions}")
print(f"\nNow refresh: http://127.0.0.1:8000/api/parent/dashboard/7/")