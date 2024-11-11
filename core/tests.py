# /workspace/shiftwise/core/tests.py

from django.test import TestCase
from django.core import mail
from .utils import send_email_notification
from django.conf import settings


class EmailNotificationTests(TestCase):
    def test_send_email_notification_success(self):
        send_email_notification(
            user_email="testuser@example.com",
            subject="Test Subject",
            message="This is a test message.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
        self.assertEqual(mail.outbox[0].body, "This is a test message.")
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn("testuser@example.com", mail.outbox[0].to)

    def test_send_email_notification_failure(self):
        # Temporarily set an invalid email backend to simulate failure
        original_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

        with self.assertRaises(Exception):
            send_email_notification(
                user_email="invalid-email",
                subject="Test Subject",
                message="This is a test message.",
            )

        # Restore original email backend
        settings.EMAIL_BACKEND = original_backend
