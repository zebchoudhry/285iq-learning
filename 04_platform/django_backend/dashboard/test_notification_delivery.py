from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from dashboard.models import NotificationLog
from dashboard.services.notification_delivery import send_parent_notification
from learning.models import Subject


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@example.com',
)
class ParentNotificationRecipientTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name='mathematics', display_name='GCSE Maths')

    def _send(self, student):
        return send_parent_notification(
            student_id=student.id,
            subject_id=self.subject.id,
            event_type='tier_change',
            priority=1,
            message='Outlook changed.',
            student_name='Test Student',
        )

    def test_sends_only_to_the_students_own_parent(self):
        from django.utils import timezone

        student = get_user_model().objects.create_user(
            username='kid1', password='x-test-pass', parent_email='parent1@example.com',
            parent_email_verified_at=timezone.now(),
        )
        get_user_model().objects.create_user(
            username='kid2', password='x-test-pass', parent_email='parent2@example.com',
            parent_email_verified_at=timezone.now(),
        )

        self.assertTrue(self._send(student))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['parent1@example.com'])
        self.assertEqual(NotificationLog.objects.count(), 1)

    def test_an_unconfirmed_parent_email_gets_nothing(self):
        """The student typed the address; its owner has not confirmed it, so no child data goes to it."""
        student = get_user_model().objects.create_user(
            username='kid4', password='x-test-pass', parent_email='stranger@example.com'
        )
        self.assertFalse(self._send(student))
        self.assertEqual(mail.outbox, [])
        self.assertEqual(NotificationLog.objects.count(), 0)

    def test_no_parent_email_sends_nothing(self):
        student = get_user_model().objects.create_user(username='kid3', password='x-test-pass')

        self.assertFalse(self._send(student))
        self.assertEqual(mail.outbox, [])
        self.assertEqual(NotificationLog.objects.count(), 0)
