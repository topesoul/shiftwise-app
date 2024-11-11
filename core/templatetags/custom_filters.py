# /workspace/shiftwise/shifts/templatetags/custom_filters.py

from django import template

register = template.Library()


@register.filter(name="format_feature")
def format_feature(value):
    """
    Formats a feature name by replacing underscores with spaces and capitalizing the first letter.
    Usage:
        {{ feature|format_feature }}
    """
    return value.replace("_", " ").capitalize()
