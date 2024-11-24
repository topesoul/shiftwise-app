# /workspace/shiftwise/home/views.py

from django.views.generic import TemplateView

from subscriptions.models import Plan


class HomeView(TemplateView):
    """
    Home view for the application, displaying subscription plans.
    Accessible to all users.
    """

    template_name = "home/home.html"
