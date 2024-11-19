# /workspace/shiftwise/subscriptions/signals.py

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from subscriptions.utils import create_stripe_customer

from .models import Subscription
from accounts.models import Agency

# Initialize logger
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Agency)
def create_stripe_customer_for_agency(sender, instance, created, **kwargs):
    if created and not instance.stripe_customer_id:
        # Create Stripe Customer
        try:
            customer = create_stripe_customer(instance)
            instance.stripe_customer_id = customer.id
            instance.save(update_fields=["stripe_customer_id"])
            logger.info(
                f"Stripe customer created for Agency: {instance.name} (ID: {customer.id})"
            )
        except Exception as e:
            logger.error(
                f"Failed to create Stripe customer for Agency {instance.name}: {e}"
            )