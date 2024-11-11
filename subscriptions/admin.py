# /workspace/shiftwise/subscriptions/admin.py

from django.contrib import admin
from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "view_limit",
        "stripe_product_id",
        "stripe_price_id",
        "description",
    )
    search_fields = ("name", "stripe_product_id", "stripe_price_id", "description")
    list_filter = ("name",)
    ordering = ("name",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "agency",
        "plan",
        "is_active",
        "current_period_start",
        "current_period_end",
        "stripe_subscription_id",
    )
    search_fields = ("agency__name", "plan__name", "stripe_subscription_id")
    list_filter = ("is_active", "plan__name")
    ordering = ("-current_period_start",)
