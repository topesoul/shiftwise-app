# /workspace/shiftwise/home/views.py

from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    Home view for the application, displaying subscription plans.
    Accessible to all users.
    """

    template_name = "home/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
