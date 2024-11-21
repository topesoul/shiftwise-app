# /workspace/shiftwise/accounts/models.py

import hashlib
import logging
import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from encrypted_model_fields.fields import EncryptedCharField

from core.constants import AGENCY_TYPE_CHOICES, ROLE_CHOICES
from core.utils import generate_unique_code, create_unique_filename

logger = logging.getLogger(__name__)


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")
    email = models.EmailField(max_length=254, unique=True)

    def __str__(self):
        return self.username


class Agency(models.Model):
    """
    Represents an agency managing multiple shifts.
    """

    name = models.CharField(max_length=255, unique=True)
    agency_code = models.CharField(max_length=20, editable=False, unique=True)
    agency_type = models.CharField(
        max_length=100,
        choices=AGENCY_TYPE_CHOICES,
        default="staffing",
    )
    is_active = models.BooleanField(default=True)
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="owned_agency",
        null=True,
        blank=True,
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    # Address Fields
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="UK", blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Agencies"

    def __str__(self):
        return f"{self.agency_code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.agency_code:
            # Generate a unique agency_code with "AG-" prefix followed by 8 uppercase characters
            self.agency_code = generate_unique_code(prefix="AG-", length=8)
        # Ensure that Agency email matches the Owner's email
        if self.owner and self.email != self.owner.email:
            self.email = self.owner.email
        super().save(*args, **kwargs)

    @property
    def is_subscription_active(self):
        """
        Checks if the agency's subscription is active.
        """
        if hasattr(self, 'subscription') and self.subscription:
            return self.subscription.is_active and self.subscription.current_period_end > timezone.now()
        else:
            return False


class Profile(models.Model):
    """
    Represents a user's profile with additional information.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True)
    travel_radius = models.FloatField(default=0.0)
    profile_picture = models.ImageField(
        upload_to=create_unique_filename, null=True, blank=True
    )
    totp_secret = EncryptedCharField(max_length=32, null=True, blank=True)
    recovery_codes = EncryptedCharField(
        max_length=500, null=True, blank=True
    )  # To store hashed codes
    monthly_view_count = models.PositiveIntegerField(default=0)
    view_count_reset_date = models.DateField(null=True, blank=True)

    # Address Fields
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="UK", blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def generate_recovery_codes(self, num_codes=5):
        """
        Generates a list of unique recovery codes, hashes them, stores them in the profile,
        and returns the plain codes to display to the user.
        """
        codes = []
        plain_codes = []
        for _ in range(num_codes):
            # Generate a unique 8-character code
            code = uuid.uuid4().hex[:8].upper()
            plain_codes.append(code)
            # Hash the code using SHA-256
            hashed_code = hashlib.sha256(code.encode()).hexdigest()
            codes.append(hashed_code)
        # Store the hashed codes as a comma-separated string
        self.recovery_codes = ",".join(codes)
        self.save()
        # Return the plain codes to be shown to the user
        return plain_codes

    def reset_view_count_if_needed(self):
        """
        Resets the monthly view count if the reset date has passed.
        """
        if (
            self.view_count_reset_date
            and timezone.now().date() >= self.view_count_reset_date
        ):
            self.monthly_view_count = 0
            self.view_count_reset_date = timezone.now().date().replace(
                day=1
            ) + timezone.timedelta(days=32)
            self.view_count_reset_date = self.view_count_reset_date.replace(day=1)
            self.save()

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def is_agency_subscription_active(self):
        """
        Checks if the associated agency's subscription is active.
        """
        return self.agency.is_subscription_active if self.agency else False

    @property
    def subscription_features(self):
        """
        Retrieves the features enabled by the agency's active subscription.
        """
        if self.user.is_superuser:
            return [
                "notifications_enabled",
                "advanced_reporting",
                "priority_support",
                "shift_management",
                "staff_performance",
                "custom_integrations",
            ]
        if self.is_agency_subscription_active and self.agency.subscription.plan:
            return self.agency.subscription.plan.get_features_list()
        return []

    def has_feature(self, feature_name):
        """
        Checks if the profile has access to a specific feature based on the subscription.
        """
        if self.user.is_superuser:
            return True
        if not self.is_agency_subscription_active:
            return False
        return feature_name in self.subscription_features

    def save(self, *args, **kwargs):
        try:
            this = Profile.objects.get(id=self.id)
            if this.profile_picture != self.profile_picture:
                if this.profile_picture:
                    if os.path.isfile(this.profile_picture.path):
                        os.remove(this.profile_picture.path)
                        logger.info(
                            f"Old profile picture deleted for user {self.user.username}."
                        )
        except Profile.DoesNotExist:
            pass
        super(Profile, self).save(*args, **kwargs)


class Invitation(models.Model):
    """
    Represents an invitation sent to a staff member.
    """

    email = models.EmailField(unique=True)
    invited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="invitations"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    invited_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        agency_name = self.agency.name if self.agency else "No Agency"
        return f"Invitation for {self.email} by {self.invited_by.username} at {agency_name}"

    def is_expired(self):
        """
        Checks if the invitation is older than 7 days.
        """
        expiration_date = self.invited_at + timezone.timedelta(days=7)
        return timezone.now() > expiration_date