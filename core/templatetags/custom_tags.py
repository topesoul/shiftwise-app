# /workspace/shiftwise/core/templatetags/custom_tags.py

from django import template
from subscriptions.models import Plan
from geopy.distance import geodesic

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    """Check if a user belongs to a group with the given name."""
    return user.groups.filter(name=group_name).exists()


@register.simple_tag
def get_distance(shift, lat, lng):
    """Calculate the distance between the shift location and a given latitude/longitude."""
    if not (shift.latitude and shift.longitude and lat and lng):
        return None
    try:
        shift_location = (float(shift.latitude), float(shift.longitude))
        completion_location = (float(lat), float(lng))
        distance = geodesic(shift_location, completion_location).miles
        return distance
    except (ValueError, TypeError):
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