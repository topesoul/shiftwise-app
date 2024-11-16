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

class ShiftCompleteView(
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, FeatureRequiredMixin, View
):
    """
    Allows agency staff or superusers to complete a shift with digital signature and location verification.
    Superusers can complete any shift without agency restrictions.
    """

    required_features = ['shift_management']

    def get(self, request, shift_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id)
        assignment = get_object_or_404(ShiftAssignment, shift=shift, worker=request.user)

        if shift.is_completed:
            messages.info(request, "This shift has already been completed.")
            return redirect("shifts:shift_detail", pk=shift.id)

        form = ShiftCompletionForm()
        context = {
            "form": form,
            "shift": shift,
        }
        return render(request, "shifts/shift_complete_modal.html", context)

    def post(self, request, shift_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id)
        assignment = get_object_or_404(ShiftAssignment, shift=shift, worker=request.user)

        if shift.is_completed:
            messages.info(request, "This shift has already been completed.")
            return redirect("shifts:shift_detail", pk=shift.id)

        form = ShiftCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract form data
            signature_data = form.cleaned_data["signature"]
            latitude = form.cleaned_data["latitude"]
            longitude = form.cleaned_data["longitude"]
            attendance_status = form.cleaned_data.get("attendance_status")

            # Handle signature
            if signature_data:
                try:
                    format, imgstr = signature_data.split(";base64,")
                    ext = format.split("/")[-1]
                    data = ContentFile(
                        base64.b64decode(imgstr),
                        name=f"shift_{shift.id}_signature_{uuid.uuid4()}.{ext}",
                    )
                    assignment.signature = data
                except Exception as e:
                    logger.exception(
                        f"Error processing signature for Shift ID {shift.id}: {e}"
                    )
                    messages.error(request, "Invalid signature data.")
                    return redirect("shifts:shift_detail", pk=shift.id)

            # Validate geolocation proximity unless user is superuser
            if not request.user.is_superuser:
                try:
                    user_lat = float(latitude)
                    user_lon = float(longitude)
                    shift_lat = float(shift.latitude)
                    shift_lon = float(shift.longitude)

                    distance = haversine_distance(
                        user_lat,
                        user_lon,
                        shift_lat,
                        shift_lon,
                        unit="miles",
                    )

                except (ValueError, TypeError) as e:
                    logger.exception(
                        f"Invalid geolocation data for Shift ID {shift.id}: {e}"
                    )
                    messages.error(request, "Invalid location data.")
                    return redirect("shifts:shift_detail", pk=shift.id)

                # Proceed with distance check
                if distance > 0.5:
                    messages.error(
                        request,
                        f"You are too far from the shift location ({distance:.2f} miles). You must be within 0.5 miles to complete the shift.",
                    )
                    return redirect("shifts:shift_detail", pk=shift.id)

            # Update assignment with completion data
            assignment.completion_latitude = latitude
            assignment.completion_longitude = longitude
            assignment.completion_time = timezone.now()

            # Set attendance status if provided
            if attendance_status:
                assignment.attendance_status = attendance_status

            # Mark shift as completed
            shift.is_completed = True
            shift.completion_time = timezone.now()

            if signature_data:
                shift.signature = data

            # Save both shift and assignment
            try:
                shift.clean(skip_date_validation=True)
                shift.save()
                assignment.save()
            except ValidationError as ve:
                messages.error(request, ve.message)
                return redirect("shifts:shift_detail", pk=shift.id)

            messages.success(request, "Shift completed successfully.")
            logger.info(f"User {request.user.username} completed Shift ID {shift_id}.")
            return redirect("shifts:shift_detail", pk=shift.id)
        else:
            messages.error(request, "Please correct the errors below.")
            return redirect("shifts:shift_detail", pk=shift.id)


class ShiftCompleteForUserView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, FeatureRequiredMixin, View
):
    """
    Allows superusers and agency managers to complete a shift on behalf of a user.
    Useful in scenarios where the user cannot complete the shift themselves.
    """

    required_features = ['shift_management']

    def get(self, request, shift_id, user_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id)
        user_to_complete = get_object_or_404(
            User, id=user_id, groups__name="Agency Staff", is_active=True
        )

        # Ensure the shift belongs to the manager's agency if not superuser
        if (
            not request.user.is_superuser
            and shift.agency != request.user.profile.agency
        ):
            messages.error(request, "You cannot complete shifts outside your agency.")
            logger.warning(
                f"User {request.user.username} attempted to complete Shift ID {shift.id} outside their agency."
            )
            return redirect("shifts:shift_detail", pk=shift.id)

        # Get or create the ShiftAssignment
        assignment, created = ShiftAssignment.objects.get_or_create(
            shift=shift, worker=user_to_complete
        )

        if shift.is_completed:
            messages.info(request, "This shift has already been completed.")
            return redirect("shifts:shift_detail", pk=shift.id)

        form = ShiftCompletionForm()
        context = {
            "form": form,
            "shift": shift,
            "user_to_complete": user_to_complete,
        }
        return render(request, "shifts/shift_complete_for_user_modal.html", context)

    def post(self, request, shift_id, user_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id)
        user_to_complete = get_object_or_404(
            User, id=user_id, groups__name="Agency Staff", is_active=True
        )

        # Ensure the shift belongs to the manager's agency if not superuser
        if (
            not request.user.is_superuser
            and shift.agency != request.user.profile.agency
        ):
            messages.error(request, "You cannot complete shifts outside your agency.")
            logger.warning(
                f"User {request.user.username} attempted to complete Shift ID {shift.id} outside their agency."
            )
            return redirect("shifts:shift_detail", pk=shift.id)

        # Get or create the ShiftAssignment
        assignment, created = ShiftAssignment.objects.get_or_create(
            shift=shift, worker=user_to_complete
        )

        if shift.is_completed:
            messages.info(request, "This shift has already been completed.")
            return redirect("shifts:shift_detail", pk=shift.id)

        form = ShiftCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract form data
            signature_data = form.cleaned_data["signature"]
            latitude = form.cleaned_data["latitude"]
            longitude = form.cleaned_data["longitude"]
            attendance_status = form.cleaned_data.get("attendance_status")

            # Handle signature
            if signature_data:
                try:
                    format, imgstr = signature_data.split(";base64,")
                    ext = format.split("/")[-1]
                    data = ContentFile(
                        base64.b64decode(imgstr),
                        name=f"shift_{shift.id}_signature_{uuid.uuid4()}.{ext}",
                    )
                    assignment.signature = data
                except Exception as e:
                    logger.exception(
                        f"Error processing signature for Shift ID {shift.id}: {e}"
                    )
                    messages.error(request, "Invalid signature data.")
                    return redirect("shifts:shift_detail", pk=shift.id)

            # If completing on behalf, you might want to bypass location validation or use shift's location
            if request.user.is_superuser or request.user.groups.filter(name="Agency Managers").exists():
                if not latitude or not longitude:
                    latitude = shift.latitude
                    longitude = shift.longitude

            # Validate geolocation proximity unless user is superuser
            if not request.user.is_superuser:
                try:
                    user_lat = float(latitude)
                    user_lon = float(longitude)
                    shift_lat = float(shift.latitude)
                    shift_lon = float(shift.longitude)

                    distance = haversine_distance(
                        user_lat,
                        user_lon,
                        shift_lat,
                        shift_lon,
                        unit="miles",
                    )

                except (ValueError, TypeError) as e:
                    logger.exception(
                        f"Invalid geolocation data for Shift ID {shift.id}: {e}"
                    )
                    messages.error(request, "Invalid location data.")
                    return redirect("shifts:shift_detail", pk=shift.id)

                # Proceed with distance check
                if distance > 0.5:
                    messages.error(
                        request,
                        f"You are too far from the shift location ({distance:.2f} miles). You must be within 0.5 miles to complete the shift.",
                    )
                    logger.info(
                        f"User {request.user.username} is too far from shift {shift.id} location ({distance:.2f} miles)."
                    )
                    return redirect("shifts:shift_detail", pk=shift.id)

            # Update assignment with completion data
            assignment.completion_latitude = latitude
            assignment.completion_longitude = longitude
            assignment.completion_time = timezone.now()

            # Set attendance status if provided
            if attendance_status:
                assignment.attendance_status = attendance_status

            # Mark shift as completed
            shift.is_completed = True
            shift.completion_time = timezone.now()

            if signature_data:
                shift.signature = data

            # Save both shift and assignment
            try:
                shift.clean(skip_date_validation=True)
                shift.save()
                assignment.save()
            except ValidationError as ve:
                messages.error(request, ve.message)
                return redirect("shifts:shift_detail", pk=shift.id)

            messages.success(
                request,
                f"Shift '{shift.name}' completed successfully for {user_to_complete.get_full_name()}.",
            )
            logger.info(
                f"Shift ID {shift.id} completed by {request.user.username} for user {user_to_complete.username}."
            )
            return redirect("shifts:shift_detail", pk=shift.id)
        else:
            messages.error(request, "Please correct the errors below.")
            return redirect("shifts:shift_detail", pk=shift.id)


class ShiftCompleteAjaxView(
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, FeatureRequiredMixin, View
):
    """
    Handles shift completion via AJAX, returning JSON responses.
    Superusers can complete any shift without agency restrictions.
    """

    required_features = ['shift_management']

    def post(self, request, shift_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id)

        # Check if the user is assigned to this shift or is a superuser
        if not (
            ShiftAssignment.objects.filter(shift=shift, worker=user).exists()
            or user.is_superuser
        ):
            return JsonResponse(
                {
                    "success": False,
                    "message": "You do not have permission to complete this shift.",
                },
                status=403,
            )

        if shift.is_completed:
            return JsonResponse(
                {"success": False, "message": "This shift has already been completed."},
                status=200,
            )

        signature = request.POST.get("signature")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        attendance_status = request.POST.get(
            "attendance_status"
        )  # Capture attendance status from AJAX

        if not all([signature, latitude, longitude]):
            return JsonResponse(
                {
                    "success": False,
                    "message": "All fields are required to complete the shift.",
                },
                status=400,
            )

        # Validate geolocation proximity (within 0.5 miles) if not superuser
        if not user.is_superuser:
            try:
                user_lat = float(latitude)
                user_lon = float(longitude)
                shift_lat = float(shift.latitude)
                shift_lon = float(shift.longitude)

                if not shift_lat or not shift_lon:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Shift location is not properly set.",
                        },
                        status=400,
                    )

                distance = haversine_distance(
                    user_lat, user_lon, shift_lat, shift_lon, unit="miles"
                )

            except (ValueError, TypeError):
                return JsonResponse(
                    {"success": False, "message": "Invalid location data."}, status=400
                )

            # Proceed with distance check
            if distance > 0.5:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "You are not within the required 0.5-mile distance to complete this shift.",
                    },
                    status=400,
                )

        # Save the signature image
        try:
            format, imgstr = signature.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"shift_{shift.id}_signature_{uuid.uuid4()}.{ext}",
            )
        except Exception as e:
            logger.exception(
                f"Error decoding signature from user {user.username} for Shift ID {shift_id}: {e}"
            )
            return JsonResponse(
                {"success": False, "message": "Invalid signature data."}, status=400
            )

        # Update shift with signature and mark as completed
        shift.signature = data
        shift.is_completed = True
        shift.completion_time = timezone.now()
        shift.save()

        # If not superuser, update the assignment
        if not user.is_superuser:
            assignment = ShiftAssignment.objects.get(shift=shift, worker=user)
            assignment.signature = data
            assignment.completion_latitude = latitude
            assignment.completion_longitude = longitude
            assignment.completion_time = timezone.now()
            assignment.attendance_status = attendance_status
            assignment.save()

        logger.info(f"User {user.username} completed Shift ID {shift_id} via AJAX.")
        return JsonResponse(
            {"success": True, "message": "Shift completed successfully."}, status=200
        )

    def get(self, request, shift_id, *args, **kwargs):
        """
        Handle invalid GET requests for this view.
        """
        return JsonResponse(
            {"success": False, "message": "Invalid request method."}, status=405
        )
