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


class GymControllerWithHistoryTests(TestCase):
    """Regression: the controller crashed ("Cannot filter a query once a slice has been taken")
    for any student who had already answered a question in the topic."""

    def test_decide_gym_mode_with_attempts_does_not_crash(self):
        from learning.models import Question, QuizAttempt

        user = User.objects.create_user(username="veteran", password="testpass")
        topic = Topic.objects.create(subject=Subject.objects.create(name="biology", display_name="Biology"), name="Cells")
        lesson = Lesson.objects.create(topic=topic, title="1.1 - Cells", content="x")
        q = Question.objects.create(lesson=lesson, question_text="Q?", correct_answer="a", question_type="short_answer")
        for ok in [True, True, False, True, False, False, True]:
            QuizAttempt.objects.create(student=user, question=q, is_correct=ok)
        result = decide_gym_mode(user.id, topic.id)
        assert result["mode"] in {"guided_practice", "drill", "mixed_practice", "instruction", "exam_sim", "mastery_maintenance"}
        assert 0 <= result["metrics_snapshot"]["recent_accuracy"] <= 1
