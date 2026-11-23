from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from learning.models import Lesson, MultipleChoiceOption, Question, QuizAttempt, Subject, Topic
from learning.services.mistake_feedback import classify_by_rules, diagnose_wrong_answer


class ClassifyByRulesTests(TestCase):
    def test_blank_answer_is_guess(self):
        self.assertEqual(classify_by_rules("", "42"), "guess")

    def test_very_fast_answer_is_guess(self):
        self.assertEqual(classify_by_rules("17", "42", time_spent_ms=1500), "guess")

    def test_near_numeric_answer_is_procedural(self):
        self.assertEqual(classify_by_rules("41", "42"), "procedural")

    def test_decimal_place_slip_is_procedural(self):
        self.assertEqual(classify_by_rules("2.5", "25"), "procedural")

    def test_far_off_answer_is_conceptual(self):
        self.assertEqual(classify_by_rules("photosynthesis", "respiration"), "conceptual")


def _make_question(**kwargs):
    subject = Subject.objects.create(name="mathematics", display_name="GCSE Maths")
    topic = Topic.objects.create(subject=subject, name="Number")
    lesson = Lesson.objects.create(topic=topic, title="Percentages", content="...")
    defaults = dict(
        lesson=lesson,
        question_text="What is 10% of 250?",
        correct_answer="25",
        explanation="10% means divide by 10, so 250 / 10 = 25.",
    )
    defaults.update(kwargs)
    return Question.objects.create(**defaults)


@override_settings(LLM_BACKEND="disabled")
class DiagnoseWithoutAITests(TestCase):
    def test_falls_back_to_rules_and_stored_explanation(self):
        q = _make_question()
        result = diagnose_wrong_answer(q, "2.5")
        self.assertEqual(result["error_type"], "procedural")
        self.assertEqual(result["source"], "rules")
        self.assertEqual(result["explanation"], q.explanation)
        self.assertNotIn("25", result["hint"])


@override_settings(LLM_BACKEND="anthropic", LLM_USE_TUTOR=True)
class DiagnoseWithAITests(TestCase):
    def test_uses_ai_classification_and_text(self):
        q = _make_question()
        reply = (
            '{"error_type": "conceptual", "hint": "Think about what percent means.",'
            ' "explanation": "Percent means out of 100, so 10% is a tenth."}'
        )
        with mock.patch("learning.services.llm_service.generate", return_value=reply):
            result = diagnose_wrong_answer(q, "240")
        self.assertEqual(result["source"], "ai")
        self.assertEqual(result["error_type"], "conceptual")
        self.assertEqual(result["label"], "Concept gap")
        self.assertIn("out of 100", result["explanation"])

    def test_bad_ai_reply_falls_back_to_rules(self):
        q = _make_question()
        with mock.patch("learning.services.llm_service.generate", return_value="not json"):
            result = diagnose_wrong_answer(q, "240")
        self.assertEqual(result["source"], "rules")
        self.assertEqual(result["explanation"], q.explanation)

    def test_ai_error_does_not_break_submission(self):
        q = _make_question()
        with mock.patch("learning.services.llm_service.generate", side_effect=RuntimeError("down")):
            result = diagnose_wrong_answer(q, "240")
        self.assertEqual(result["source"], "rules")

    def test_guess_skips_ai_call(self):
        q = _make_question()
        with mock.patch("learning.services.llm_service.generate") as gen:
            result = diagnose_wrong_answer(q, "")
        gen.assert_not_called()
        self.assertEqual(result["error_type"], "guess")


@override_settings(LLM_BACKEND="disabled")
class SubmitAttemptSavesErrorTypeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="student", password="x-test-pass", subscription_status="pro_monthly"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_wrong_short_answer_gets_feedback_and_error_type(self):
        q = _make_question()
        r = self.client.post("/api/attempts/", {"question_id": q.id, "answer": "2.5"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["is_correct"])
        self.assertEqual(r.data["mistake_feedback"]["error_type"], "procedural")
        self.assertEqual(QuizAttempt.objects.get(question=q).error_type, "procedural")

    def test_wrong_multiple_choice_uses_option_text(self):
        q = _make_question(question_type="multiple_choice", correct_answer="")
        MultipleChoiceOption.objects.create(question=q, option_text="25", is_correct=True)
        wrong = MultipleChoiceOption.objects.create(question=q, option_text="2500", is_correct=False)
        r = self.client.post(
            "/api/attempts/", {"question_id": q.id, "selected_option_id": wrong.id}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("mistake_feedback", r.data)
        self.assertNotEqual(QuizAttempt.objects.get(question=q).error_type, "none")

    def test_correct_answer_has_no_feedback(self):
        q = _make_question()
        r = self.client.post("/api/attempts/", {"question_id": q.id, "answer": "25"}, format="json")
        self.assertTrue(r.data["is_correct"])
        self.assertNotIn("mistake_feedback", r.data)
        self.assertEqual(QuizAttempt.objects.get(question=q).error_type, "none")
