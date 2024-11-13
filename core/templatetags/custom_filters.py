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
    Checks if the user has a specific feature enabled.
    Assumes user.profile.subscription.plan.features is a dictionary.
    """
    if (
        user.is_authenticated
        and hasattr(user, 'profile')
        and hasattr(user.profile, 'subscription')
        and user.profile.subscription
        and hasattr(user.profile.subscription, 'plan')
        and hasattr(user.profile.subscription.plan, 'features')
    ):
        return user.profile.subscription.plan.features.get(feature_name, False)
    return False

@register.filter(name='has_feature')
def has_feature(user, feature_name):
    """
    Checks if the user's subscription includes the specified feature.
    Usage: {% if user|has_feature:"shift_management" %}
    """
    if not user.is_authenticated:
        return False
    return feature_name in getattr(user.profile, 'subscription_features', [])