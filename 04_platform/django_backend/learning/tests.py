"""Tests for learning app - API and quiz."""
import pytest
pytestmark = pytest.mark.django_db

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from learning.models import Subject, Topic, Lesson, Question, StudentProgress
from learning.services.gym_controller import decide_gym_mode

User = get_user_model()


class SubjectProgressAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='student1', password='testpass123')
        self.client.force_login(self.user)
        # Create minimal subject/topic/lesson for progress
        self.subject = Subject.objects.create(name='mathematics', display_name='Mathematics', is_active=True)
        self.topic = Topic.objects.create(subject=self.subject, name='Algebra', is_active=True, order=0)
        self.lesson = Lesson.objects.create(topic=self.topic, title='Intro', content='Content', estimated_duration=10, is_active=True, order=0)

    def test_subject_progress_returns_list(self):
        response = self.client.get('/api/subject-progress/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn('subject_id', data[0])
        self.assertIn('progress_percent', data[0])

    def test_subject_progress_requires_auth(self):
        self.client.logout()
        response = self.client.get('/api/subject-progress/')
        self.assertEqual(response.status_code, 403)


class QuizStartAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='quizuser', password='testpass123')
        self.client.force_login(self.user)
        self.subject = Subject.objects.create(name='mathematics', display_name='Mathematics', is_active=True)
        self.topic = Topic.objects.create(subject=self.subject, name='Algebra', is_active=True, order=0)
        self.lesson = Lesson.objects.create(topic=self.topic, title='Intro', content='C', estimated_duration=10, is_active=True, order=0)
        self.question = Question.objects.create(lesson=self.lesson, question_text='What is 2+2?', correct_answer='4', is_active=True)

    def test_quiz_start_returns_mode_and_content(self):
        response = self.client.post('/api/quiz/start/', data={'topic_id': self.topic.id}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('mode', data)
        self.assertIn('content_type', data)

    def test_quiz_start_requires_auth(self):
        self.client.logout()
        response = self.client.post('/api/quiz/start/', data={'topic_id': self.topic.id}, content_type='application/json')
        self.assertEqual(response.status_code, 403)


class GymControllerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='gymuser', password='testpass123')
        self.subject = Subject.objects.create(name='mathematics', display_name='Mathematics', is_active=True)
        self.topic = Topic.objects.create(subject=self.subject, name='Algebra', is_active=True, order=0)

    def test_decide_gym_mode_no_attempts(self):
        result = decide_gym_mode(self.user.id, self.topic.id)
        self.assertIn('mode', result)
        self.assertIn('content', result)
        self.assertIn(result['mode'], ('instruction', 'guided_practice', 'drill', 'mixed_practice', 'exam_sim', 'mastery_maintenance'))
