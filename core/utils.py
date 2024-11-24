# /workspace/shiftwise/core/utils.py

import hashlib
import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_notification(user_id, message, subject="Notification", url=None):
    """
    Sends an email notification to the user with the given user_id.
    """
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        recipient = user.email
        full_message = (
            f"{message}\n\nVisit: {settings.SITE_URL}{url}" if url else message
        )
        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
        logger.info(f"Notification sent to {user.username} at {recipient}.")
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist.")


def assign_user_to_group(user, group_name):
    """
    Assigns the given user to the specified group.
    """
    try:
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        logger.info(f"User {user.username} assigned to group '{group_name}'.")
    except Exception as e:
        logger.error(
            f"Error assigning user {user.username} to group '{group_name}': {e}"
        )


def generate_unique_code(prefix="", length=6):
    """
    Generates a unique code with an optional prefix.
    """
    return f"{prefix}{uuid.uuid4().hex[:length].upper()}"


def create_unique_filename(instance, filename):
    """
    Generates a unique filename using UUID to prevent name collisions.
    """
    ext = filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("uploads/", unique_filename)


def send_email_notification(
    user_email, subject, message, from_email=None, html_message=None, **kwargs
):
    """
    Sends an email notification to the specified user.
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
