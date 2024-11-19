# /workspace/shiftwise/accounts/context_processors.py

import logging
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification
from subscriptions.models import Plan, Subscription

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
    needs_upgrade = False
    unread_notifications_count = 0
    dashboard_url = ""

    subscription = None  # Initialize subscription variable

    if user.is_authenticated:
        try:
            # Determine dashboard URL based on user role
            if is_superuser:
                dashboard_url = reverse("accounts:superuser_dashboard")
            elif is_agency_owner or is_agency_manager:
                dashboard_url = reverse("accounts:agency_dashboard")
            elif is_agency_staff:
                dashboard_url = reverse("accounts:staff_dashboard")
            else:
                dashboard_url = reverse("accounts:profile")
        except Exception as e:
            logger.exception(f"Error determining dashboard_url for user {user.username}: {e}")
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
                    subscription_features = subscription.plan.get_features_list()
                    # Update can_manage_shifts based on features
                    can_manage_shifts = (
                        is_superuser
                        or is_agency_manager
                        or "Shift Management" in subscription_features
                    )

                    # Implement Usage Limit Check based on number of shifts
                    current_shift_count = agency.shifts.count()
                    if subscription.plan.shift_management and subscription.plan.shift_limit:
                        if current_shift_count >= subscription.plan.shift_limit:
                            needs_upgrade = True
                            logger.debug(
                                f"Agency '{agency.name}' has reached its shift limit ({current_shift_count}/{subscription.plan.shift_limit}). Upgrade needed."
                            )
            else:
                logger.warning(f"User {user.username} does not have an associated agency or subscription.")
        except ObjectDoesNotExist:
            logger.warning(f"User {user.username} does not have a profile or agency.")
        except Exception as e:
            logger.exception(f"Error in context processor: {e}")

        # Fetch unread notifications for the user
        notifications = Notification.objects.filter(user=user, read=False).order_by("-created_at")
        unread_notifications_count = notifications.count()

        # Add all features if user is superuser
        if is_superuser:
            all_features = [
                "Notifications Enabled",
                "Advanced Reporting",
                "Priority Support",
                "Shift Management",
                "Staff Performance Tracking",
                "Custom Integrations",
            ]
            subscription_features = list(set(subscription_features + all_features))
            logger.debug(f"Superuser '{user.username}' assigned all features.")

        # Attach subscription_features to user object for 'has_feature' filter
        setattr(user, "subscription_features", subscription_features)

    # Retrieve all active plans and group them
    plans = Plan.objects.filter(is_active=True).order_by("name", "billing_cycle")
    plan_dict = defaultdict(dict)
    for plan in plans:
        if plan.billing_cycle.lower() == "monthly":
            plan_dict[plan.name]["monthly_plan"] = plan
        elif plan.billing_cycle.lower() == "yearly":
            plan_dict[plan.name]["yearly_plan"] = plan

    for plan_name, plans in plan_dict.items():
        available_plans.append(
            {
                "name": plan_name,
                "description": plans.get("monthly_plan", plans.get("yearly_plan")).description,
                "monthly_plan": plans.get("monthly_plan"),
                "yearly_plan": plans.get("yearly_plan"),
            }
        )

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
        "subscription": subscription,
    }