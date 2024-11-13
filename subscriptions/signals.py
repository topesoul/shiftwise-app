# /workspace/shiftwise/subscriptions/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Subscription
from core.utils import send_notification
from django.urls import reverse
import logging

# Initialize logger
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after a subscription is created or updated.
    """
    if created:
        message = f"Your subscription to the {instance.plan.name} Plan has been activated."
        subject = "Subscription Activated"
    else:
        message = f"Your subscription has been updated to the {instance.plan.name} Plan."
        subject = "Subscription Updated"

    url = reverse("subscriptions:manage_subscription")

    # Notify the agency owner
    try:
        agency_owner = instance.agency.owner
        if agency_owner:
            send_notification(
                user_id=agency_owner.id,
                message=message,
                subject=subject,
                url=url
            )
            logger.info(f"Notification sent to agency owner: {agency_owner.username}")
        else:
            logger.warning(f"Agency {instance.agency.name} has no associated owner.")
    except AttributeError as e:
        logger.exception(f"Error accessing agency owner: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in subscription_post_save: {e}")
