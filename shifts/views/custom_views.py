# /workspace/shiftwise/shifts/views/custom_views.py

import logging

from django.contrib.auth import get_user_model
from django.shortcuts import render

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()


def custom_permission_denied_view(request, exception):
    """
    Render a custom 403 Forbidden page.
    """
    return render(request, "403.html", status=403)


def custom_page_not_found_view(request, exception):
    """
    Render a custom 404 Not Found page.
    """
    return render(request, "404.html", status=404)


def custom_server_error_view(request):
    """
    Render a custom 500 Server Error page.
    """
    return render(request, "500.html", status=500)
