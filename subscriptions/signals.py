# /workspace/shiftwise/subscriptions/signals.py

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from subscriptions.utils import create_stripe_customer
from .models import Subscription, Plan
from accounts.models import Agency

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Agency)
def handle_agency_creation(sender, instance, created, **kwargs):
    if created and not instance.stripe_customer_id:
        with transaction.atomic():
            # Create Stripe Customer
            try:
                customer = create_stripe_customer(instance)
                instance.stripe_customer_id = customer.id
                instance.save(update_fields=["stripe_customer_id"])
                logger.info(f"Stripe customer created for Agency: {instance.name} (ID: {customer.id})")
            except Exception as e:
                logger.error(f"Failed to create Stripe customer for Agency {instance.name}: {e}")
                raise  # Re-raise to rollback the transaction

            # Assign the Default 'Basic' Plan if Exists
            try:
                basic_plan = Plan.objects.get(name="Basic", billing_cycle="monthly")
            except Plan.DoesNotExist:
                basic_plan = None
                logger.error(f"Basic plan does not exist. Cannot create subscription for agency {instance.name}.")

            if basic_plan:
                # Check if subscription already exists for the agency
                existing_subscription = Subscription.objects.filter(agency=instance).first()
                if not existing_subscription:
                    Subscription.objects.create(
                        agency=instance,
                        plan=basic_plan,
                        is_active=False,  # Initially inactive until payment
                        current_period_start=timezone.now(),
                        current_period_end=timezone.now() + timezone.timedelta(days=30),
                    )
                    logger.info(f"Subscription created for agency {instance.name} with plan {basic_plan.name}.")
                else:
                    logger.warning(f"Subscription already exists for agency {instance.name}.")
            else:
                logger.error(f"Failed to create subscription for agency {instance.name} because Basic plan is missing.")