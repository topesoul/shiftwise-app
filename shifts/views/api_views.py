# /workspace/shiftwise/shifts/views/api_views.py

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View

from core.mixins import FeatureRequiredMixin
from shifts.models import Shift

# Initialize logger
logger = logging.getLogger(__name__)


class ShiftDetailsAPIView(LoginRequiredMixin, View):
    """
    Provides shift details in JSON format.
    """

    def get(self, request, shift_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id)
        shift_data = {
            "id": shift.id,
            "name": shift.name,
            "shift_date": shift.shift_date,
            "start_time": (
                shift.start_time.strftime("%H:%M:%S") if shift.start_time else ""
            ),
            "end_time": shift.end_time.strftime("%H:%M:%S") if shift.end_time else "",
            "status": shift.status,
            "capacity": shift.capacity,
            "available_slots": shift.available_slots,
            "is_full": shift.is_full,
            "agency": shift.agency.name if shift.agency else "No Agency",
            "latitude": shift.latitude,
            "longitude": shift.longitude,
        }
        logger.debug(
            f"Shift details requested for shift ID {shift_id} by user {request.user.username}"
        )
        return JsonResponse({"shift": shift_data})


class APIAccessView(LoginRequiredMixin, FeatureRequiredMixin, TemplateView):
    """
    Displays API access information for users with the 'custom_integrations' feature.
    """

    template_name = "shifts/api_access.html"
    required_features = ["custom_integrations"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_endpoint"] = self.request.build_absolute_uri("/api/shift/")
        logger.debug(f"API Access page accessed by user {self.request.user.username}")
        return context
