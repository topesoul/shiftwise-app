# /workspace/shiftwise/core/templatetags/custom_tags.py

from django import template
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
