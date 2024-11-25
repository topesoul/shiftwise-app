# /workspace/shiftwise/accounts/signals.py

import logging
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from PIL import Image, ImageOps

from .models import Profile

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


@receiver(post_save, sender=Profile)
def handle_profile_picture_resize(sender, instance, **kwargs):
    """
    Resizes the profile picture to a maximum size to optimize storage.
    """
    if instance.profile_picture:
        try:
            # Open the image from the storage backend
            img_temp = BytesIO(instance.profile_picture.read())
            img = Image.open(img_temp)
            max_size = (500, 500)
            img = ImageOps.exif_transpose(img)
            img.thumbnail(max_size, Image.LANCZOS)

            # Convert image mode if necessary
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and 'transparency' in img.info):
                img = img.convert("RGB")

            # Save the processed image back to storage
            img_io = BytesIO()
            img_format = img.format if img.format else "JPEG"  # Default to JPEG if format is undefined
            img.save(img_io, format=img_format)
            instance.profile_picture.save(
                instance.profile_picture.name,
                ContentFile(img_io.getvalue()),
                save=False,
            )
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
        # Delete the old picture using the storage backend
        old_picture.delete(save=False)
        logger.info(f"Deleted old profile picture for user {instance.user.username}.")

