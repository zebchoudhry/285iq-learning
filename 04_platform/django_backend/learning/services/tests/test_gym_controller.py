import pytest
pytestmark = pytest.mark.django_db

from django.test import TestCase
from django.contrib.auth import get_user_model

from learning.services.gym_controller import decide_gym_mode
from learning.models import Subject, Topic, Lesson

User = get_user_model()


class GymControllerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )

        self.subject = Subject.objects.create(
            name="mathematics",
            display_name="Mathematics"
        )

        self.topic = Topic.objects.create(
            subject=self.subject,
            name="Fractions"
        )

        Lesson.objects.create(
            topic=self.topic,
            title="Introduction to Fractions",
            content="Basic fractions",
            lesson_type="theory",
            difficulty_level=2,
            estimated_duration=10
        )

    def test_instruction_mode_when_no_attempts(self):
        result = decide_gym_mode(
            student_id=self.user.id,
            topic_id=self.topic.id
        )

        self.assertEqual(result["mode"], "instruction")
        self.assertEqual(result["reason"], "insufficient_data")
        self.assertIn("content", result)
        self.assertEqual(result["content"]["content_type"], "lessons")
