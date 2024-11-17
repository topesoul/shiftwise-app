# /workspace/shiftwise/shifts/views/dashboard_views.py

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.mixins import FeatureRequiredMixin
from notifications.models import Notification
from shifts.models import Shift

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()


class DashboardView(LoginRequiredMixin, FeatureRequiredMixin, TemplateView):
    template_name = "shifts/dashboard.html"

    required_features = ["shift_management"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Fetch shifts based on user role
        if user.is_superuser:
            shifts = Shift.objects.all()
        elif user.groups.filter(name="Agency Managers").exists():
            shifts = Shift.objects.filter(agency=user.profile.agency)
        elif user.groups.filter(name="Agency Staff").exists():
            shifts = Shift.objects.filter(shiftassignment__worker=user)
        else:
            shifts = Shift.objects.none()

        context["shifts"] = shifts.distinct()

        # Fetch unread notifications
        context["notifications"] = user.notifications.filter(read=False).order_by(
            "-created_at"
        )

        logger.debug(
            f"Dashboard accessed by user {user.username}. Number of shifts: {shifts.count()}, Unread notifications: {context['notifications'].count()}"
        )

        return context
