# /workspace/shiftwise/subscriptions/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Subscription
from django.contrib.auth.models import Group
from core.mixins import send_notification
from django.urls import reverse
from django.conf import settings


@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after a subscription is created or updated.
    """
    if created:
        message = (
            f"Your subscription to the {instance.plan.name} Plan has been activated."
        )
    else:
        message = (
            f"Your subscription has been updated to the {instance.plan.name} Plan."
        )

    url = reverse("subscriptions:manage_subscription")

    # Notify the agency owner
    agency_owner = instance.agency.owner
    if agency_owner:
        send_notification(agency_owner.id, message, icon="fas fa-subscript", url=url)
