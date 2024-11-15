# /workspace/shiftwise/shifts/signals.py

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Shift, ShiftAssignment
from core.utils import (
    send_notification,
    send_email_notification,
)
from django.contrib.auth import get_user_model
import logging

User = get_user_model()

# Initialize logger
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Shift)
def shift_created_or_updated(sender, instance, created, **kwargs):
    if created:
        message = f"A new shift '{instance.name}' has been created."
        subject = "New Shift Created"
    else:
        message = f"The shift '{instance.name}' has been updated."
        subject = "Shift Updated"

    # Send real-time notification to agency managers
    agency_managers = User.objects.filter(
        groups__name="Agency Managers", profile__agency=instance.agency
    )
    for manager in agency_managers:
        send_notification(user_id=manager.id, message=message)
        # Send email notification
        send_email_notification(
            user_email=manager.email, subject=subject, message=message
        )
    logger.info(f"Shift '{instance.name}' {'created' if created else 'updated'} and notifications sent to managers.")

@receiver(pre_delete, sender=Shift)
def shift_deleted(sender, instance, **kwargs):
    message = f"The shift '{instance.name}' has been deleted."
    subject = "Shift Deleted"

    # Send real-time notification to agency managers
    agency_managers = User.objects.filter(
        groups__name="Agency Managers", profile__agency=instance.agency
    )
    for manager in agency_managers:
        send_notification(user_id=manager.id, message=message)
        # Send email notification
        send_email_notification(
            user_email=manager.email, subject=subject, message=message
        )
    logger.info(f"Shift '{instance.name}' deleted and notifications sent to managers.")

@receiver(post_save, sender=ShiftAssignment)
def shift_assignment_created(sender, instance, created, **kwargs):
    if created:
        message = f"You have been assigned to shift '{instance.shift.name}'."
        subject = "Shift Assignment"

        # Send real-time notification to the worker
        send_notification(user_id=instance.worker.id, message=message)
        # Send email notification to the worker
        send_email_notification(
            user_email=instance.worker.email, subject=subject, message=message
        )
        logger.info(f"ShiftAssignment created: Worker {instance.worker.username} assigned to shift '{instance.shift.name}'.")

@receiver(pre_delete, sender=ShiftAssignment)
def shift_assignment_deleted(sender, instance, **kwargs):
    message = f"You have been unassigned from shift '{instance.shift.name}'."
    subject = "Shift Unassignment"

    # Send real-time notification to the worker
    send_notification(user_id=instance.worker.id, message=message)
    # Send email notification to the worker
    send_email_notification(
        user_email=instance.worker.email, subject=subject, message=message
    )
    logger.info(f"ShiftAssignment deleted: Worker {instance.worker.username} unassigned from shift '{instance.shift.name}'.")
