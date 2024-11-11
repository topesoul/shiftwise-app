# /workspace/shiftwise/subscriptions/models.py

from django.conf import settings
from django.db import models


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

    name = models.CharField(max_length=100)
    description = models.TextField()
    stripe_product_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True
    )
    stripe_price_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True
    )
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLES)
    features = models.JSONField(default=dict, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    view_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text="Maximum number of views allowed per month."
    )
    is_active = models.BooleanField(default=True)
    is_recommended = models.BooleanField(default=False)

    # Feature flags
    notifications_enabled = models.BooleanField(default=False)
    advanced_reporting = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    max_staff_members = models.IntegerField(default=10)  # Varies per plan
    shift_management = models.BooleanField(default=False)

    class Meta:
        unique_together = ("name", "billing_cycle")

    def __str__(self):
        return f"{self.name} ({self.get_billing_cycle_display()})"


class Subscription(models.Model):
    """
    Represents a user's subscription.
    """

    agency = models.OneToOneField(
        "accounts.Agency", on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_expired = models.BooleanField(default=False)

    def __str__(self):
        plan_name = self.plan.name if self.plan else "No Plan"
        return f"Subscription for {self.agency.name} - {plan_name}"
