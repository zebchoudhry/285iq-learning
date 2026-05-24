"""
Comprehensive test setup: creates minimal test data for platform verification.
All DB work runs inside test functions (no module-level DB access).
"""
import pytest
from datetime import timedelta
import random

pytestmark = pytest.mark.django_db


def test_setup_creates_minimal_data():
    """Create students, subjects, topics, lessons, questions, attempts, exam settings; assert counts."""
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from users.models import Student, UserProfile
    from learning.models import Subject, Topic, Lesson, Question, QuizAttempt, StudentExamSettings

    User = get_user_model()

    test_students = [
        {'username': 'kia', 'password': 'password123', 'first_name': 'Kia', 'last_name': 'Test'},
        {'username': 'alex', 'password': 'password123', 'first_name': 'Alex', 'last_name': 'Morgan'},
        {'username': 'sarah', 'password': 'password123', 'first_name': 'Sarah', 'last_name': 'Lee'},
    ]

    students_dict = {}
    for student_data in test_students:
        try:
            student = Student.objects.get(username=student_data['username'])
        except Student.DoesNotExist:
            student = Student.objects.create_user(
                username=student_data['username'],
                password=student_data['password'],
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                grade_level='Year 11'
            )
            UserProfile.objects.create(
                student=student,
                total_xp=random.randint(500, 3000),
                current_level=random.randint(1, 10),
                daily_streak=random.randint(0, 30),
                school_rank=random.randint(1, 50)
            )
        students_dict[student_data['username']] = student

    subjects_data = [
        {'name': 'mathematics', 'display_name': 'Mathematics'},
        {'name': 'biology', 'display_name': 'Biology'},
        {'name': 'chemistry', 'display_name': 'Chemistry'},
        {'name': 'physics', 'display_name': 'Physics'},
    ]

    subjects_dict = {}
    for subj_data in subjects_data:
        subject, _ = Subject.objects.get_or_create(
            name=subj_data['name'],
            defaults={'display_name': subj_data['display_name'], 'is_active': True}
        )
        subjects_dict[subj_data['name']] = subject

    topics_data = {
        'mathematics': ['Algebra', 'Geometry', 'Trigonometry'],
        'biology': ['Cell Biology', 'Organisation', 'Evolution'],
        'chemistry': ['Atomic Structure', 'Bonding', 'Reactions'],
        'physics': ['Forces', 'Energy', 'Waves'],
    }

    for subject_name, topics_list in topics_data.items():
        subject = subjects_dict[subject_name]
        for idx, topic_name in enumerate(topics_list):
            Topic.objects.get_or_create(
                subject=subject,
                name=topic_name,
                defaults={'order': idx, 'is_active': True}
            )

    for topic in Topic.objects.all():
        for i in range(2):
            Lesson.objects.get_or_create(
                topic=topic,
                title=f"{topic.name} - Lesson {i+1}",
                defaults={
                    'content': f'Learning materials for {topic.name}',
                    'estimated_duration': 45,
                    'order': i,
                    'is_active': True
                }
            )

    questions_list = list(Question.objects.all())
    kia = students_dict['kia']
    if questions_list:
        for _ in range(50):
            question = random.choice(questions_list)
            is_correct = random.random() < 0.65
            QuizAttempt.objects.create(
                student=kia,
                question=question,
                is_correct=is_correct,
                error_type='none' if is_correct else random.choice(['conceptual', 'procedural', 'guess']),
                attempted_at=timezone.now() - timedelta(days=random.randint(0, 28))
            )

    exam_date = timezone.now() + timedelta(days=120)
    for subject in Subject.objects.all():
        StudentExamSettings.objects.get_or_create(
            student=kia,
            subject=subject,
            defaults={
                'exam_date': exam_date.date(),
                'target_grade': random.choice([5, 6, 7, 8, 9]),
                'exam_board': 'aqa',
                'tier': 'higher'
            }
        )

    assert Student.objects.count() >= 1
    assert Subject.objects.count() >= 1
    assert Topic.objects.count() >= 1
    assert Lesson.objects.count() >= 1
