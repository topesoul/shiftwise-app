from django import template

register = template.Library()

@register.simple_tag
def has_permission(user):
    """
    Returns True if the user is authenticated and is a superuser or an Agency Manager.
    """
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Agency Managers').exists())