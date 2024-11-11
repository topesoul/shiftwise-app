# /workspace/shiftwise/core/utils.py

import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.conf import settings

# Initialize logger
logger = logging.getLogger(__name__)


def send_notification(user_id, message, icon="fas fa-info-circle", url=""):
    """
    Sends a real-time notification to a specific user via WebSocket.
    """
    channel_layer = get_channel_layer()
    group_name = f"user_{user_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "message": message,
            "icon": icon,
            "url": url,
        },
    )
    logger.debug(f"Real-time notification sent to user {user_id}: {message}")


def send_email_notification(
    user_email, subject, message, from_email=None, html_message=None, **kwargs
):
    """
    Sends an email notification to the specified user.

    Parameters:
    - user_email (str): Recipient's email address.
    - subject (str): Subject line of the email.
    - message (str): Plain-text body of the email.
    - from_email (str, optional): Sender's email address. Defaults to settings.DEFAULT_FROM_EMAIL.
    - html_message (str, optional): HTML body of the email.
    - **kwargs: Additional arguments for Django's send_mail function.
    """
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    try:
        send_mail(
            subject,
            message,
            from_email,
            [user_email],
            fail_silently=False,
            html_message=html_message,
            **kwargs,
        )
        logger.info(
            f"Email notification sent to {user_email} with subject '{subject}'."
        )
    except Exception as e:
        logger.exception(f"Failed to send email notification to {user_email}: {e}")
