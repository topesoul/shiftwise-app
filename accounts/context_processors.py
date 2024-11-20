# /workspace/shiftwise/accounts/context_processors.py

import logging
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification
from subscriptions.models import Plan

# Initialize logger
logger = logging.getLogger(__name__)


def user_roles_and_subscriptions(request):
    user = request.user
    is_superuser = user.is_superuser if user.is_authenticated else False
    is_agency_owner = (
        user.groups.filter(name="Agency Owners").exists()
        if user.is_authenticated
        else False
    )
    is_agency_manager = (
        user.groups.filter(name="Agency Managers").exists()
        if user.is_authenticated
        else False
    )
    is_agency_staff = (
        user.groups.filter(name="Agency Staff").exists()
        if user.is_authenticated
        else False
    )
    has_active_subscription = False
    available_plans = []
    current_plan = None
    subscription_features = []
    can_manage_shifts = False
    notifications = []
    unread_notifications_count = 0  # Initialize unread notifications count
    needs_upgrade = False  # Flag to indicate if an upgrade is needed

    # Define all possible features with display names
    ALL_FEATURES = [
        ("notifications_enabled", "Notifications Enabled"),
        ("advanced_reporting", "Advanced Reporting"),
        ("priority_support", "Priority Support"),
        ("shift_management", "Shift Management"),
        ("staff_performance", "Staff Performance Tracking"),
        ("custom_integrations", "Custom Integrations"),
    ]

    # Retrieve all active plans
    plans = Plan.objects.filter(is_active=True).order_by("name", "billing_cycle")

    # Group plans by name
    plan_dict = defaultdict(dict)
    for plan in plans:
        if plan.billing_cycle.lower() == "monthly":
            plan_dict[plan.name]["monthly_plan"] = plan
        elif plan.billing_cycle.lower() == "yearly":
            plan_dict[plan.name]["yearly_plan"] = plan

    # Structure available_plans as a list of dictionaries
    for plan_name, plans in plan_dict.items():
        # Ensure at least one plan exists
        if not plans.get("monthly_plan") and not plans.get("yearly_plan"):
            logger.warning(f"No monthly or yearly plan found for {plan_name}. Skipping.")
            continue

        # Use the description from either monthly or yearly plan
        description = (
            plans.get("monthly_plan").description
            if plans.get("monthly_plan")
            else plans.get("yearly_plan").description
        )

        available_plans.append(
            {
                "name": plan_name,
                "description": description,
                "monthly_plan": plans.get("monthly_plan"),
                "yearly_plan": plans.get("yearly_plan"),
            }
        )

    dashboard_url = ""
    if user.is_authenticated:
        try:
            if is_superuser:
                dashboard_url = reverse("accounts:superuser_dashboard")
            elif is_agency_owner or is_agency_manager:
                dashboard_url = reverse("accounts:agency_dashboard")
            elif is_agency_staff:
                dashboard_url = reverse("accounts:staff_dashboard")
            else:
                dashboard_url = reverse("accounts:profile")
        except Exception as e:
            logger.exception(
                f"Error determining dashboard_url for user {user.username}: {e}"
            )
            dashboard_url = reverse("accounts:profile")

        try:
            profile = user.profile
            agency = profile.agency
            if agency and hasattr(agency, 'subscription'):
                subscription = agency.subscription
                if subscription.is_active and subscription.current_period_end > timezone.now():
                    has_active_subscription = True
                    current_plan = subscription.plan
                    # Collect features
                    subscription_features = profile.subscription_features
                    # Update can_manage_shifts based on features
                    can_manage_shifts = profile.has_feature("shift_management") or is_superuser or is_agency_manager

                    # Implement Usage Limit Check based on number of shifts
                    current_shift_count = agency.shifts.count()
                    if subscription.plan.shift_management and subscription.plan.shift_limit:
                        if current_shift_count >= subscription.plan.shift_limit:
                            needs_upgrade = True
                            logger.debug(
                                f"Agency '{agency.name}' has reached the shift limit ({current_shift_count}/{subscription.plan.shift_limit}). Upgrade needed."
                            )
            else:
                logger.warning(
                    f"User {user.username} does not have an associated agency or subscription."
                )
        except ObjectDoesNotExist:
            # User does not have a profile or agency
            logger.warning(f"User {user.username} does not have a profile or agency.")
        except Exception as e:
            logger.exception(f"Error in context processor: {e}")

        # Fetch unread notifications for the user
        notifications = Notification.objects.filter(user=user, read=False).order_by("-created_at")
        unread_notifications_count = notifications.count()

    return {
        "is_superuser": is_superuser,
        "is_agency_owner": is_agency_owner,
        "is_agency_manager": is_agency_manager,
        "is_agency_staff": is_agency_staff,
        "has_active_subscription": has_active_subscription,
        "available_plans": available_plans,
        "current_plan": current_plan,
        "subscription_features": subscription_features,
        "can_manage_shifts": can_manage_shifts,
        "notifications": notifications,
        "unread_notifications_count": unread_notifications_count,
        "needs_upgrade": needs_upgrade,
        "dashboard_url": dashboard_url,
        "all_features": ALL_FEATURES,
    }
