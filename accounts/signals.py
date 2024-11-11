# /workspace/shiftwise/accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, Agency, Subscription, Plan
from subscriptions.utils import create_stripe_customer
from core.utils import send_notification
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


# Signal to create Subscription and Stripe Customer when Agency is created
@receiver(post_save, sender=Agency)
def create_subscription_and_stripe_customer_for_agency(sender, instance, created, **kwargs):
    if created:
        # **Create Stripe Customer**
        try:
            customer = create_stripe_customer(instance)
            instance.stripe_customer_id = customer.id
            instance.save(update_fields=['stripe_customer_id'])
            logger.info(f"Stripe customer created for Agency: {instance.name} (ID: {customer.id})")
        except Exception as e:
            logger.error(f"Failed to create Stripe customer for Agency {instance.name}: {e}")
            # Depending on your business logic, you might want to handle this differently

        # **Assign the Default 'Basic' Plan if Exists**
        try:
            basic_plan = Plan.objects.get(name="Basic", billing_cycle="monthly")
        except Plan.DoesNotExist:
            basic_plan = None
            logger.error(
                f"Basic plan does not exist. Cannot create subscription for agency {instance.name}."
            )

        if basic_plan:
            Subscription.objects.create(
                agency=instance,
                plan=basic_plan,
                is_active=False,  # Initially inactive until payment
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timezone.timedelta(days=30),
            )
            logger.info(
                f"Subscription created for agency {instance.name} with plan {basic_plan.name}."
            )
        else:
            logger.error(
                f"Failed to create subscription for agency {instance.name} because Basic plan is missing."
            )


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Creates or updates the Profile associated with a User.
    """
    if created:
        Profile.objects.create(user=instance)
        logger.info(f"Profile created for user {instance.username}.")
    else:
        instance.profile.save()
        logger.info(f"Profile updated for user {instance.username}.")

    # Send notification
    message = "Your profile has been updated successfully."
    url = reverse("accounts:profile")
    send_notification(instance.id, message, icon="fas fa-user-edit", url=url)
