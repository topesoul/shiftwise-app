# /workspace/shiftwise/core/templatetags/custom_tags.py

from django import template

from shiftwise.utils import haversine_distance
from subscriptions.models import Plan

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    """Check if a user belongs to a group with the given name."""
    return user.groups.filter(name=group_name).exists()


@register.simple_tag
def calculate_distance(shift, user_lat, user_lon):
    """
    Calculates the distance between the user and the shift location.
    Usage: {{ shift|calculate_distance:user_lat:user_lon }}
    """
    if shift.latitude and shift.longitude and user_lat and user_lon:
        distance = haversine_distance(
            user_lat,
            user_lon,
            shift.latitude,
            shift.longitude,
            unit="miles",
        )
        return distance
    else:
        return None


@register.filter(name="get_plan_name")
def get_plan_name(price_id):
    """
    Retrieves the local Plan name based on the Stripe Price ID.
    Usage: {{ price_id|get_plan_name }}
    """
    try:
        plan = Plan.objects.get(stripe_price_id=price_id)
        return plan.name
    except Plan.DoesNotExist:
        return "Unknown Plan"
