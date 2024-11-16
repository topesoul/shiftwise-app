import base64
import csv
import uuid
import logging
import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.base import ContentFile
from django.db.models import Q, Count, F, Sum, FloatField, ExpressionWrapper, Prefetch
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView, View, TemplateView, FormView
)
from django_filters.views import FilterView
from accounts.models import Profile, Agency
from notifications.models import Notification
from accounts.forms import StaffCreationForm, StaffUpdateForm
from shifts.models import Shift, ShiftAssignment, StaffPerformance
from shifts.forms import ShiftForm, ShiftCompletionForm, StaffPerformanceForm, AssignWorkerForm, UnassignWorkerForm
from shifts.filters import ShiftFilter
from shifts.utils import is_shift_full, is_user_assigned
from core.mixins import AgencyOwnerRequiredMixin, SubscriptionRequiredMixin, AgencyManagerRequiredMixin, AgencyStaffRequiredMixin, FeatureRequiredMixin
from shiftwise.utils import haversine_distance,  generate_shift_code

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()

class ShiftBookView(
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, FeatureRequiredMixin, View
):
    """
    Allows agency staff or superusers to book a shift based on availability and proximity.
    Superusers can book any shift without agency restrictions.
    """

    required_features = ['shift_management']

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
            logger.info(f"User {user.username} attempted to book a full shift {shift.id}.")
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
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, FeatureRequiredMixin, View
):
    """
    Allows agency staff or superusers to unbook a shift.
    Superusers can unbook any shift without agency restrictions.
    """

    required_features = ['shift_management']

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