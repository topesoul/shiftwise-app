# /workspace/shiftwise/shifts/templatetags/custom_tags.py

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
    if shift.latitude and shift.longitude and lat and lng:
        try:
            # Convert latitude and longitude to floats
            shift_lat = float(shift.latitude)
            shift_lng = float(shift.longitude)
            completion_lat = float(lat)
            completion_lng = float(lng)
            shift_location = (shift_lat, shift_lng)
            completion_location = (completion_lat, completion_lng)
            return geodesic(shift_location, completion_location).miles
        except (ValueError, TypeError):
            return None
    return None
