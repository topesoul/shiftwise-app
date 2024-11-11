# /workspace/shiftwise/accounts/tasks.py

from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Notification
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task
def create_notification_task(user_id, message, icon=None, url=None):
    """
    Celery task to create a notification for a user.
    """
    try:
        user = User.objects.get(id=user_id)
        Notification.objects.create(user=user, message=message, icon=icon, url=url)
        logger.info(f"Notification created for user {user.username}: {message}")
    except User.DoesNotExist:
        logger.error(
            f"User with id {user_id} does not exist. Failed to create notification."
        )


@shared_task
def send_email_task(subject, message, recipient_list):
    """
    Celery task to send an email.
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_list}: {subject}")
    except Exception as e:
        logger.exception(f"Failed to send email to {recipient_list}: {e}")
