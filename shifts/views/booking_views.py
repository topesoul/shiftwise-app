# /workspace/shiftwise/shifts/views/booking_views.py

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from core.mixins import (
    AgencyStaffRequiredMixin,
    FeatureRequiredMixin,
    SubscriptionRequiredMixin,
)
from shifts.models import Shift, ShiftAssignment
from shifts.utils import is_shift_full, is_user_assigned
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
    Allows agency staff or superusers to book a shift based on availability and proximity.
    Superusers can book any shift without agency restrictions.
    """

    required_features = ["shift_management"]

    def post(self, request, shift_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id)

        # Check permissions
        if not (user.groups.filter(name="Agency Staff").exists() or user.is_superuser):
            messages.error(request, "You do not have permission to book shifts.")
            logger.warning(
                f"User {user.username} attempted to book shift {shift.id} without proper permissions."
            )
            return redirect("shifts:shift_list")

        # For non-superusers, ensure the shift belongs to their agency
        if not user.is_superuser and shift.agency != user.profile.agency:
            messages.error(request, "You cannot book shifts outside your agency.")
            logger.warning(
                f"User {user.username} attempted to book shift {shift.id} outside their agency."
            )
            return redirect("shifts:shift_list")

        # Check if the shift is full
        if is_shift_full(shift):
            messages.error(request, "This shift is already full.")
            logger.info(
                f"User {user.username} attempted to book a full shift {shift.id}."
            )
            return redirect("shifts:shift_list")

        # Check if the user has already booked the shift
        if is_user_assigned(shift, user):
            messages.info(request, "You have already booked this shift.")
            logger.info(f"User {user.username} attempted to re-book shift {shift.id}.")
            return redirect("shifts:shift_detail", pk=shift_id)

        # Check proximity if not superuser
        if not user.is_superuser:
            if (
                user.profile.latitude
                and user.profile.longitude
                and shift.latitude
                and shift.longitude
            ):
                distance = haversine_distance(
                    user.profile.latitude,
                    user.profile.longitude,
                    shift.latitude,
                    shift.longitude,
                    unit="miles",
                )
                if distance > user.profile.travel_radius:
                    messages.error(
                        request,
                        f"You are too far from the shift location ({distance:.2f} miles).",
                    )
                    logger.info(
                        f"User {user.username} is too far from shift {shift.id} location ({distance:.2f} miles)."
                    )
                    return redirect("shifts:shift_detail", pk=shift_id)
            else:
                messages.error(
                    request, "Your location or the shift location is not set."
                )
                logger.warning(
                    f"User {user.username} attempted to book shift {shift.id} without proper location data."
                )
                return redirect("shifts:shift_detail", pk=shift_id)

        # Create a ShiftAssignment
        ShiftAssignment.objects.create(shift=shift, worker=user)
        messages.success(request, "You have successfully booked the shift.")
        logger.info(f"User {user.username} booked shift {shift.id}.")
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
    Allows agency staff or superusers to unbook a shift.
    Superusers can unbook any shift without agency restrictions.
    """

    required_features = ["shift_management"]

    def post(self, request, shift_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id)

        # Check permissions
        if not (user.groups.filter(name="Agency Staff").exists() or user.is_superuser):
            messages.error(request, "You do not have permission to unbook shifts.")
            logger.warning(
                f"User {user.username} attempted to unbook shift {shift.id} without proper permissions."
            )
            return redirect("shifts:shift_list")

        # For non-superusers, ensure the shift belongs to their agency
        if not user.is_superuser and shift.agency != user.profile.agency:
            messages.error(request, "You cannot unbook shifts outside your agency.")
            logger.warning(
                f"User {user.username} attempted to unbook shift {shift.id} outside their agency."
            )
            return redirect("shifts:shift_list")

        # Retrieve the ShiftAssignment
        assignment = ShiftAssignment.objects.filter(shift=shift, worker=user).first()
        if not assignment:
            messages.error(request, "You have not booked this shift.")
            logger.info(
                f"User {user.username} attempted to unbook shift {shift.id} without existing booking."
            )
            return redirect("shifts:shift_list")

        # Delete the ShiftAssignment
        assignment.delete()
        messages.success(request, "You have successfully unbooked the shift.")
        logger.info(f"User {user.username} unbooked shift {shift.id}.")
        return redirect("shifts:shift_detail", pk=shift_id)

    def get(self, request, shift_id, *args, **kwargs):
        """
        Redirect GET requests to the shift detail page.
        """
        return redirect("shifts:shift_detail", pk=shift_id)
