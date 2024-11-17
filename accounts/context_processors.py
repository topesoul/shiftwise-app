# accounts/context_processors.py

import logging
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification
from subscriptions.models import Plan, Subscription

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

    needs_upgrade = False  # Flag to indicate if an upgrade is needed

    unread_notifications_count = 0  # Initialize unread notifications count

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
        available_plans.append(
            {
                "name": plan_name,
                "description": plans.get(
                    "monthly_plan", plans.get("yearly_plan")
                ).description,
                "monthly_plan": plans.get("monthly_plan"),
                "yearly_plan": plans.get("yearly_plan"),
            }
        )

    dashboard_url = ""
    if user.is_authenticated:
        try:
            if user.is_superuser:
                dashboard_url = reverse("accounts:superuser_dashboard")
            elif (
                user.groups.filter(name="Agency Owners").exists()
                or user.groups.filter(name="Agency Managers").exists()
            ):
                dashboard_url = reverse("accounts:agency_dashboard")
            elif user.groups.filter(name="Agency Staff").exists():
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
            if agency:
                subscription = (
                    Subscription.objects.filter(
                        agency=agency,
                        is_active=True,
                        current_period_end__gt=timezone.now(),
                    )
                    .select_related("plan")
                    .first()
                )
                if subscription and subscription.plan:
                    has_active_subscription = True
                    current_plan = subscription.plan
                    # Collect features
                    if subscription.plan.notifications_enabled:
                        subscription_features.append("notifications_enabled")
                    if subscription.plan.advanced_reporting:
                        subscription_features.append("advanced_reporting")
                    if subscription.plan.priority_support:
                        subscription_features.append("priority_support")
                    if subscription.plan.shift_management:
                        subscription_features.append("shift_management")
                    if subscription.plan.staff_performance:
                        subscription_features.append("staff_performance")
                    if subscription.plan.custom_integrations:
                        subscription_features.append("custom_integrations")
                    # Update can_manage_shifts based on features
                    can_manage_shifts = (
                        is_superuser
                        or is_agency_manager
                        or "shift_management" in subscription_features
                    )

                    # Implement Usage Limit Check based on number of shifts
                    current_shift_count = agency.shifts.count()
                    if (
                        subscription.plan.shift_management
                        and subscription.plan.shift_limit
                    ):
                        if current_shift_count >= subscription.plan.shift_limit:
                            needs_upgrade = True
                            logger.debug(
                                f"Agency '{agency.name}' has reached its shift limit ({current_shift_count}/{subscription.plan.shift_limit}). Upgrade needed."
                            )
            else:
                logger.warning(
                    f"User {user.username} does not have an associated agency."
                )
        except ObjectDoesNotExist:
            # User does not have a profile or agency
            logger.warning(f"User {user.username} does not have a profile or agency.")
        except Exception as e:
            logger.exception(f"Error in context processor: {e}")

        # Fetch unread notifications for the user
        notifications = Notification.objects.filter(user=user, read=False).order_by(
            "-created_at"
        )
        unread_notifications_count = notifications.count()

        # Add all features if user is superuser
        if is_superuser:
            all_features = [
                "notifications_enabled",
                "advanced_reporting",
                "priority_support",
                "shift_management",
                "staff_performance",
                "custom_integrations",
            ]
            subscription_features = list(set(subscription_features + all_features))
            logger.debug(f"Superuser '{user.username}' assigned all features.")

        # Attach subscription_features to user object for 'has_feature' filter
        setattr(user, "subscription_features", subscription_features)

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
    }
