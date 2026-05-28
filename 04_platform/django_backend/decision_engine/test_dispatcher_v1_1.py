"""Smoke test: dispatcher routes to v1.1 when flag is set."""
from datetime import date
from django.test import TestCase, override_settings

from users.models import Student
from learning.models import Subject, Topic, Lesson, Question
from dashboard.models import ExamBoard


@override_settings(DECISION_ENGINE_VERSION='1.1')
class DispatcherV1_1SmokeTest(TestCase):
    def setUp(self):
        # Re-import dispatcher after override so the module-level
        # flag re-evaluates. importlib.reload is the cleanest way.
        import importlib, decision_engine.dispatcher as d
        importlib.reload(d)
        self.dispatcher = d

        board = ExamBoard.objects.create(name='AQA', code='AQA')
        self.subject = Subject.objects.create(
            exam_board=board, name='maths', display_name='Maths',
        )
        self.topic = Topic.objects.create(
            subject=self.subject, name='Algebra',
        )
        self.student = Student.objects.create_user(
            username='dispatch_test', password='testpass123',
        )

    def tearDown(self):
        # Restore dispatcher to default v1.0 for other tests.
        import importlib, decision_engine.dispatcher as d
        importlib.reload(d)

    def test_dispatcher_routes_to_v1_1(self):
        result = self.dispatcher.evaluate_student_subject(
            student_id=self.student.id,
            subject_id=self.subject.id,
            exam_date=date.today().replace(year=date.today().year + 1),
            target_grade=6,
            previous_tier=None,
        )
        # v1.1-specific keys must be present
        assert 'predicted_grade_range' in result, result
        assert 'rating_confidence' in result, result
        assert 'tier' in result               # backward compat
        assert 'attainment_band' in result    # backward compat
        # With no attempts, band is 0 (insufficient data)
        assert result['attainment_band'] == 0
        assert result['predicted_grade_range'] == (0, 0)
