# /workspace/shiftwise/accounts/models.py

import hashlib
import logging
import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedCharField

from subscriptions.models import Plan, Subscription

logger = logging.getLogger(__name__)


class User(AbstractUser):
    ROLE_CHOICES = (
        ("staff", "Staff"),
        ("agency_manager", "Agency Manager"),
        ("agency_owner", "Agency Owner"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")
    email = models.EmailField(max_length=254, unique=True)  # Ensuring unique emails

    def __str__(self):
        return self.username


class Agency(models.Model):
    """
    Represents an agency managing multiple shifts.
    """

    name = models.CharField(max_length=255, unique=True)
    agency_code = models.CharField(max_length=50, unique=True, blank=True)
    agency_type = models.CharField(
        max_length=100,
        choices=[
            ("staffing", "Staffing"),
            ("healthcare", "Healthcare"),
        ],
        default="staffing",
    )
    is_active = models.BooleanField(default=True)
    address_line1 = models.CharField(max_length=255, default="Unknown Address")
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, default="Unknown City")
    county = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="UK")
    postcode = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="owned_agency",
        null=True,
        blank=True,
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Agencies"

    def __str__(self):
        return f"{self.agency_code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.agency_code:
            self.agency_code = f"AG-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default="UK")
    postcode = models.CharField(max_length=20, blank=True, null=True)
    travel_radius = models.FloatField(default=0.0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    totp_secret = EncryptedCharField(max_length=32, null=True, blank=True)
    recovery_codes = EncryptedCharField(
        max_length=500, null=True, blank=True
    )  # To store hashed codes
    monthly_view_count = models.PositiveIntegerField(default=0)
    view_count_reset_date = models.DateField(null=True, blank=True)

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
    def subscription_features(self):
        if self.subscription and self.subscription.plan:
            features = []
            if self.subscription.plan.notifications_enabled:
                features.append("notifications_enabled")
            if self.subscription.plan.advanced_reporting:
                features.append("advanced_reporting")
            if self.subscription.plan.priority_support:
                features.append("priority_support")
            if self.subscription.plan.shift_management:
                features.append("shift_management")
            if self.subscription.plan.staff_performance:
                features.append("staff_performance")
            if self.subscription.plan.custom_integrations:
                features.append("custom_integrations")
            return features
        return []

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
            pass  # New profile, no action needed
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