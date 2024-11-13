# /workspace/shiftwise/core/utils.py

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

logger = logging.getLogger(__name__)

User = get_user_model()


def send_notification(user_id, message, subject="Notification", url=""):
    """
    Sends an email notification to a specific user.

    Parameters:
    - user_id (int): ID of the user to notify.
    - message (str): The message content.
    - subject (str): Subject of the email.
    - url (str): Optional URL to include in the message.
    """
    try:
        user = User.objects.get(id=user_id)
        user_email = user.email

        if not user_email:
            logger.error(f"User {user.username} does not have an email address.")
            return

        full_message = message
        if url:
            # Assuming SITE_URL is set in settings
            site_url = getattr(settings, 'SITE_URL', '')
            if site_url:
                full_message += f"\n\nYou can view more details here: {site_url}{url}"
            else:
                full_message += f"\n\nYou can view more details here: {url}"

        send_mail(
            subject=subject,
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.debug(f"Email notification sent to user {user.username} ({user_email}): {subject}")
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} does not exist. Notification not sent.")
    except Exception as e:
        logger.exception(f"Failed to send notification to user ID {user_id}: {e}")


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
