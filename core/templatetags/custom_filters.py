# /workspace/shiftwise/core/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name="format_feature")
def format_feature(value):
    """Formats a feature name by replacing underscores with spaces and capitalizing the first letter."""
    return value.replace("_", " ").capitalize()

@register.filter(name="has_feature")
def has_feature(user, feature_name):
    """
    Checks if the user's subscription includes the specified feature.
    Usage: {% if user|has_feature:"shift_management" %}
    """
    if not user.is_authenticated:
        return False
    return feature_name in getattr(user.profile, 'subscription_features', [])
