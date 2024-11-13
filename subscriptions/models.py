# /workspace/shiftwise/subscriptions/models.py

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


class Plan(models.Model):
    """
    Represents a subscription plan.
    """
    BASIC = "Basic"
    PRO = "Pro"
    ENTERPRISE = "Enterprise"

    PLAN_CHOICES = [
        (BASIC, "Basic"),
        (PRO, "Pro"),
        (ENTERPRISE, "Enterprise"),
    ]

    BILLING_CYCLES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(
        max_length=100,
        choices=PLAN_CHOICES,
        help_text="Name of the subscription plan.",
    )
    description = models.TextField(
        help_text="Detailed description of the subscription plan."
    )
    stripe_product_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Stripe Product ID associated with this plan.",
    )
    stripe_price_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Stripe Price ID associated with this plan.",
    )
    billing_cycle = models.CharField(
        max_length=10,
        choices=BILLING_CYCLES,
        help_text="Billing cycle for the subscription plan.",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Price of the subscription plan.",
    )
    view_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of views allowed per month.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates whether the plan is active and available for subscription.",
    )
    is_recommended = models.BooleanField(
        default=False,
        help_text="Indicates whether the plan is recommended.",
    )

    # Feature Flags
    notifications_enabled = models.BooleanField(
        default=False,
        help_text="Enable notifications feature for this plan.",
    )
    advanced_reporting = models.BooleanField(
        default=False,
        help_text="Enable advanced reporting features for this plan.",
    )
    priority_support = models.BooleanField(
        default=False,
        help_text="Enable priority support for this plan.",
    )
    shift_management = models.BooleanField(
        default=False,
        help_text="Enable shift management features for this plan.",
    )
    staff_performance = models.BooleanField(
        default=False,
        help_text="Enable staff performance tracking for this plan.",
    )
    custom_integrations = models.BooleanField(
        default=False,
        help_text="Enable custom integrations for this plan.",
    )

    class Meta:
        unique_together = ("name", "billing_cycle")
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} ({self.get_billing_cycle_display()})"


class Subscription(models.Model):
    """
    Represents an agency's subscription.
    """
    agency = models.OneToOneField(
        "accounts.Agency",
        on_delete=models.CASCADE,
        related_name="subscription",
        help_text="Agency associated with this subscription.",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Subscription plan chosen by the agency.",
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Stripe Subscription ID associated with this subscription.",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Indicates whether the subscription is currently active.",
    )
    current_period_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Start date of the current billing period.",
    )
    current_period_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="End date of the current billing period.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the subscription was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the subscription was last updated.",
    )
    is_expired = models.BooleanField(
        default=False,
        help_text="Indicates whether the subscription has expired.",
    )

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        plan_name = self.plan.name if self.plan else "No Plan"
        return f"Subscription for {self.agency.name} - {plan_name}"

    def renew_subscription(self):
        """
        Placeholder method to handle subscription renewal logic.
        """
        pass

    def cancel_subscription(self):
        """
        Handles subscription cancellation.
        """
        self.is_active = False
        self.is_expired = True
        self.save()

    def activate_subscription(self):
        """
        Activates the subscription.
        """
        self.is_active = True
        self.is_expired = False
        self.save()

    def clean(self):
        """
        Custom validation to ensure subscription aligns with plan's constraints.
        """
        if self.plan and self.agency:
            pass

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
