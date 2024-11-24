# /workspace/shiftwise/shifts/signals.py

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse

from core.utils import send_email_notification, send_notification

from .models import Shift, ShiftAssignment

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

    # Retrieve agency managers associated with the shift's agency
    agency_managers = User.objects.filter(
        groups__name="Agency Managers", profile__agency=instance.agency
    )

    for manager in agency_managers:
        # Send email notification to agency managers
        send_notification(
            user_id=manager.id,
            message=message,
            subject=subject,
            url=reverse("accounts:agency_dashboard"),
        )
    logger.info(
        f"Shift '{instance.name}' {'created' if created else 'updated'} and notifications sent to managers."
    )


@receiver(pre_delete, sender=Shift)
def shift_deleted(sender, instance, **kwargs):
    message = f"The shift '{instance.name}' has been deleted."
    subject = "Shift Deleted"

    # Retrieve agency managers associated with the shift's agency
    agency_managers = User.objects.filter(
        groups__name="Agency Managers", profile__agency=instance.agency
    )

    for manager in agency_managers:
        # Send email notification to agency managers
        send_notification(
            user_id=manager.id,
            message=message,
            subject=subject,
            url=reverse("accounts:agency_dashboard"),
        )
    logger.info(f"Shift '{instance.name}' deleted and notifications sent to managers.")


@receiver(post_save, sender=ShiftAssignment)
def shift_assignment_created(sender, instance, created, **kwargs):
    if created:
        message = f"You have been assigned to shift '{instance.shift.name}'."
        subject = "Shift Assignment"

        # Send email notification to the worker
        send_notification(
            user_id=instance.worker.id,
            message=message,
            subject=subject,
            url=reverse("accounts:staff_dashboard"),
        )
        logger.info(
            f"ShiftAssignment created: Worker {instance.worker.username} assigned to shift '{instance.shift.name}'."
        )


@receiver(pre_delete, sender=ShiftAssignment)
def shift_assignment_deleted(sender, instance, **kwargs):
    message = f"You have been unassigned from shift '{instance.shift.name}'."
    subject = "Shift Unassignment"

    # Send email notification to the worker
    send_notification(
        user_id=instance.worker.id,
        message=message,
        subject=subject,
        url=reverse("accounts:staff_dashboard"),
    )
    logger.info(
        f"ShiftAssignment deleted: Worker {instance.worker.username} unassigned from shift '{instance.shift.name}'."
    )
