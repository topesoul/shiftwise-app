# /workspace/shiftwise/core/templatetags/custom_filters.py

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


@register.filter(name="has_feature")
def has_feature(user, feature_name):
    """
    Checks if the user's subscription includes the specified feature.
    Superusers have access to all features.
    Usage: {% if user|has_feature:"shift_management" %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.has_feature(feature_name)
    except AttributeError:
        return False


@register.filter(name="is_in")
def is_in(value, list_values):
    """
    Checks if the given value is in the provided comma-separated list.
    Usage: {% if some_var|is_in:"shift_list,shift_detail" %}...{% endif %}
    """
    if not value:
        return False
    if isinstance(list_values, str):
        list_values = [item.strip() for item in list_values.split(",")]
    return value in list_values


@register.filter(name="attr")
def attr(obj, attr_name):
    """
    Retrieves the attribute named attr_name from obj.
    Usage: {{ obj|attr:"attribute_name" }}
    """
    return getattr(obj, attr_name, False)