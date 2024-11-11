# /workspace/shiftwise/accounts/context_processors.py

from subscriptions.models import Plan, Subscription
from django.utils import timezone
from django.contrib.auth.models import Group
from collections import defaultdict

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

    can_manage_shifts = False  # New Flag

    if user.is_authenticated:
        try:
            profile = user.profile
            agency = profile.agency
            if agency:
                subscription = Subscription.objects.filter(
                    agency=agency, is_active=True, current_period_end__gt=timezone.now()
                ).first()
                if subscription:
                    has_active_subscription = True
                    current_plan = subscription.plan
                    # Collect features
                    if hasattr(subscription.plan, 'notifications_enabled') and subscription.plan.notifications_enabled:
                        subscription_features.append("notifications_enabled")
                    if hasattr(subscription.plan, 'advanced_reporting') and subscription.plan.advanced_reporting:
                        subscription_features.append("advanced_reporting")
                    if hasattr(subscription.plan, 'priority_support') and subscription.plan.priority_support:
                        subscription_features.append("priority_support")
                    if hasattr(subscription.plan, 'shift_management') and subscription.plan.shift_management:
                        subscription_features.append("shift_management")
                        # Update can_manage_shifts
                        can_manage_shifts = is_superuser or is_agency_manager
        except AttributeError:
            # User does not have a profile or agency
            pass

        # Retrieve all active plans
        plans = Plan.objects.filter(is_active=True).order_by("name", "billing_cycle")

        # Group plans by name
        plan_dict = defaultdict(dict)
        for plan in plans:
            if plan.billing_cycle.lower() == 'monthly':
                plan_dict[plan.name]['monthly_plan'] = plan
            elif plan.billing_cycle.lower() == 'yearly':
                plan_dict[plan.name]['yearly_plan'] = plan
            # Add more billing cycles if needed

        # Structure available_plans as a list of dictionaries
        for plan_name, plans in plan_dict.items():
            available_plans.append({
                "name": plan_name,
                "monthly_plan": plans.get('monthly_plan'),
                "yearly_plan": plans.get('yearly_plan'),
            })

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
    }