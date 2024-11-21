# /workspace/shiftwise/accounts/signals.py

import logging
import os
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from PIL import Image, ImageOps
from .models import Agency, Profile
from core.utils import send_notification

logger = logging.getLogger(__name__)

User = get_user_model()


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
    url = reverse("accounts:profile")  # Now reverse is defined
    send_notification(instance.id, message, subject=subject, url=url)


@receiver(post_save, sender=Profile)
def handle_profile_picture_resize(sender, instance, **kwargs):
    """
    Resizes the profile picture to a maximum size to optimize storage.
    """
    if instance.profile_picture:
        try:
            img = Image.open(instance.profile_picture.path)
            max_size = (500, 500)
            img = ImageOps.exif_transpose(img)
            img.thumbnail(max_size, Image.ANTIALIAS)
            img.save(instance.profile_picture.path)
            logger.info(f"Profile picture resized for user {instance.user.username}.")
        except Exception as e:
            logger.error(f"Error resizing profile picture for {instance.user.username}: {e}")


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
                logger.info(
                    f"Deleted old profile picture for user {instance.user.username}."
                )
            except Exception as e:
                logger.error(f"Error deleting old profile picture: {e}")
