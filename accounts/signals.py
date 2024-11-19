# /workspace/shiftwise/accounts/signals.py

import logging
import os

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from core.utils import send_notification
from subscriptions.utils import create_stripe_customer

from .models import Agency, Plan, Profile, Subscription

logger = logging.getLogger(__name__)

User = get_user_model()


# Signal to create Subscription and Stripe Customer when Agency is created
@receiver(post_save, sender=Agency)
def create_subscription_and_stripe_customer_for_agency(
    sender, instance, created, **kwargs
):
    if created:
        with transaction.atomic():
            # **Create Stripe Customer**
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
                raise  # Re-raise to rollback the transaction

            # **Assign the Default 'Basic' Plan if Exists**
            try:
                basic_plan = Plan.objects.get(name="Basic", billing_cycle="monthly")
            except Plan.DoesNotExist:
                basic_plan = None
                logger.error(
                    f"Basic plan does not exist. Cannot create subscription for agency {instance.name}."
                )

            if basic_plan:
                # Check if subscription already exists for the agency
                existing_subscription = Subscription.objects.filter(
                    agency=instance
                ).first()
                if not existing_subscription:
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
                    logger.warning(
                        f"Subscription already exists for agency {instance.name}."
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

    # Send notification via email
    subject = "Profile Update Notification"
    message = "Your profile has been updated successfully."
    url = reverse("accounts:profile")
    send_notification(instance.id, message, subject=subject, url=url)


@receiver(post_save, sender=Profile)
def resize_profile_picture(sender, instance, **kwargs):
    """
    Resizes the profile picture to a maximum size to optimize storage.
    """
    if instance.profile_picture:
        try:
            img = Image.open(instance.profile_picture.path)
            max_size = (500, 500)
            img.thumbnail(max_size, Image.ANTIALIAS)
            img.save(instance.profile_picture.path)
            logger.info(f"Profile picture resized for user {instance.user.username}.")
        except Exception as e:
            logger.error(f"Error resizing profile picture: {e}")



@receiver(pre_save, sender=Profile)
def delete_old_profile_picture(sender, instance, **kwargs):
    """
    Deletes the old profile picture file when a new one is uploaded.
    """
    if not instance.pk:
        return

    try:
        old_profile = Profile.objects.get(pk=instance.pk)
    except Profile.DoesNotExist:
        return

    old_picture = old_profile.profile_picture
    new_picture = instance.profile_picture
    if old_picture and old_picture != new_picture:
        if os.path.isfile(old_picture.path):
            try:
                os.remove(old_picture.path)
                logger.info(f"Deleted old profile picture for user {instance.user.username}.")
            except Exception as e:
                logger.error(f"Error deleting old profile picture: {e}")