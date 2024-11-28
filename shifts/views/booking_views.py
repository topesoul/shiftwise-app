# /workspace/shiftwise/shifts/views/booking_views.py

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from core.mixins import (AgencyStaffRequiredMixin, FeatureRequiredMixin,
                         SubscriptionRequiredMixin)
from shifts.models import Shift, ShiftAssignment
from shiftwise.utils import haversine_distance

# Initialize logger
logger = logging.getLogger(__name__)


class ShiftBookView(
    LoginRequiredMixin,
    AgencyStaffRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    View,
):
    """
    Allows agency staff to book a shift based on availability and proximity.
    """

    required_features = ["shift_management"]

    def post(self, request, shift_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)

        # Check permissions: Only agency staff can book shifts
        if not user.groups.filter(name="Agency Staff").exists():
            messages.error(request, "Only agency staff can book shifts.")
            return redirect("shifts:shift_list")

        # Ensure the shift belongs to the user's agency
        if shift.agency != user.profile.agency:
            messages.error(request, "You cannot book shifts outside your agency.")
            return redirect("shifts:shift_list")

        # Check if the shift is full
        if shift.is_full:
            messages.error(request, "This shift is already full.")
            return redirect("shifts:shift_list")

        # Check if the user has already booked the shift
        if ShiftAssignment.objects.filter(shift=shift, worker=user).exists():
            messages.info(request, "You have already booked this shift.")
            return redirect("shifts:shift_detail", pk=shift_id)

        # Check proximity
        profile = user.profile
        shift_lat = shift.latitude
        shift_lon = shift.longitude
        user_lat = profile.latitude
        user_lon = profile.longitude
        travel_radius = profile.travel_radius

        if (
            user_lat is not None
            and user_lon is not None
            and shift_lat is not None
            and shift_lon is not None
        ):
            distance = haversine_distance(
                user_lat, user_lon, shift_lat, shift_lon, unit="miles"
            )
            if distance > travel_radius:
                messages.error(
                    request,
                    f"You are too far from the shift location ({distance:.2f} miles).",
                )
                return redirect("shifts:shift_detail", pk=shift_id)
        else:
            messages.error(request, "Your location or the shift location is not set.")
            return redirect("shifts:shift_detail", pk=shift_id)

        # Create a ShiftAssignment
        try:
            ShiftAssignment.objects.create(shift=shift, worker=user)
            messages.success(request, "You have successfully booked the shift.")
            logger.info(f"User {user.username} booked shift {shift.id} successfully.")
            return redirect("shifts:shift_detail", pk=shift_id)
        except Exception as e:
            messages.error(
                request,
                "An unexpected error occurred while booking the shift. Please try again.",
            )
            logger.exception(
                f"Error booking shift {shift.id} for user {user.username}: {e}"
            )
            return redirect("shifts:shift_detail", pk=shift_id)

    def get(self, request, shift_id, *args, **kwargs):
        """
        Redirect GET requests to the shift detail page.
        """
        return redirect("shifts:shift_detail", pk=shift_id)


class ShiftUnbookView(
    LoginRequiredMixin,
    AgencyStaffRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    View,
):
    """
    Allows agency staff to unbook a shift.
    """

    required_features = ["shift_management"]

    def post(self, request, shift_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)

        # Check permissions: Only agency staff can unbook shifts
        if not user.groups.filter(name="Agency Staff").exists():
            messages.error(request, "Only agency staff can unbook shifts.")
            return redirect("shifts:shift_list")

        # Ensure the shift belongs to the user's agency
        if shift.agency != user.profile.agency:
            messages.error(request, "You cannot unbook shifts outside your agency.")
            return redirect("shifts:shift_list")

        # Retrieve the ShiftAssignment
        assignment = ShiftAssignment.objects.filter(shift=shift, worker=user).first()
        if not assignment:
            messages.error(request, "You have not booked this shift.")
            return redirect("shifts:shift_detail", pk=shift_id)

        # Delete the ShiftAssignment
        try:
            assignment.delete()
            messages.success(
                request, f"You have been unbooked from the shift: {shift.name}."
            )
            logger.info(
                f"User {user.username} unbooked from shift {shift.id} successfully."
            )
            return redirect("shifts:shift_detail", pk=shift_id)
        except Exception as e:
            messages.error(
                request,
                "An error occurred while unbooking the shift. Please try again.",
            )
            logger.exception(
                f"Error unbooking shift {shift.id} for user {user.username}: {e}"
            )
            return redirect("shifts:shift_detail", pk=shift_id)

    def get(self, request, shift_id, *args, **kwargs):
        """
        Redirect GET requests to the shift detail page.
        """
        return redirect("shifts:shift_detail", pk=shift_id)
