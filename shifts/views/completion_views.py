# /workspace/shiftwise/shifts/views/completion_views.py

import base64
import logging
import uuid

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View

from core.mixins import (AgencyManagerRequiredMixin, FeatureRequiredMixin,
                         SubscriptionRequiredMixin)
from shifts.forms import ShiftCompletionForm
from shifts.models import Shift, ShiftAssignment
from shiftwise.utils import haversine_distance

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()


class ShiftCompleteView(
    LoginRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    View,
):
    """
    Allows agency staff or superusers to complete a shift with digital signature and location verification.
    Superusers can complete any shift without agency restrictions.
    """

    required_features = ["shift_management"]

    def get(self, request, shift_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)

        # Ensure the user is assigned to the shift or is a superuser
        if not (
            request.user.is_superuser
            or ShiftAssignment.objects.filter(shift=shift, worker=request.user).exists()
        ):
            messages.error(request, "You are not assigned to this shift.")
            return redirect("shifts:shift_detail", pk=shift.id)

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
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)
        user = request.user

        # Ensure the shift date is not in the future
        if shift.shift_date > timezone.now().date():
            messages.error(request, "Cannot complete a shift scheduled in the future.")
            return redirect("shifts:shift_detail", pk=shift.id)

        # Ensure the user is assigned to the shift or is a superuser
        if not (
            user.is_superuser
            or ShiftAssignment.objects.filter(shift=shift, worker=user).exists()
        ):
            messages.error(request, "You are not assigned to this shift.")
            return redirect("shifts:shift_detail", pk=shift.id)

        if shift.is_completed:
            messages.info(request, "This shift has already been completed.")
            return redirect("shifts:shift_detail", pk=shift.id)

        form = ShiftCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract form data
            signature_data = form.cleaned_data.get("signature")
            latitude = form.cleaned_data.get("latitude")
            longitude = form.cleaned_data.get("longitude")
            attendance_status = form.cleaned_data.get("attendance_status")

            # Handle signature if provided
            if signature_data:
                try:
                    format, imgstr = signature_data.split(";base64,")
                    ext = format.split("/")[-1]
                    data = ContentFile(
                        base64.b64decode(imgstr),
                        name=f"shift_{shift.id}_signature_{uuid.uuid4()}.{ext}",
                    )
                except Exception as e:
                    logger.exception(
                        f"Error processing signature for Shift ID {shift.id}: {e}"
                    )
                    messages.error(request, "Invalid signature data.")
                    return redirect("shifts:shift_detail", pk=shift.id)
            else:
                data = None  # No signature provided

            # Validate geolocation proximity unless user is superuser
            if not user.is_superuser:
                if latitude and longitude and shift.latitude and shift.longitude:
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
                            f"You are too far from the shift location ({distance:.2f} miles).",
                        )
                        return redirect("shifts:shift_detail", pk=shift.id)
                else:
                    # If geo data is not provided, allow manual address
                    pass  # No distance check if location is not provided

            # Get or create the ShiftAssignment
            assignment, created = ShiftAssignment.objects.get_or_create(
                shift=shift, worker=user
            )

            # Ensure worker's profile has an agency
            if not user.profile.agency:
                messages.error(
                    request, "Your profile is not associated with any agency."
                )
                return redirect("accounts:profile")

            # Ensure worker's agency matches shift's agency
            if shift.agency != user.profile.agency:
                messages.error(
                    request, "You can only complete shifts within your agency."
                )
                return redirect("shifts:shift_detail", pk=shift.id)

            # Update assignment with completion data if provided
            if data:
                assignment.signature = data
            if latitude and longitude:
                assignment.completion_latitude = latitude
                assignment.completion_longitude = longitude
            assignment.completion_time = timezone.now()

            # Set attendance status if provided
            if attendance_status:
                assignment.attendance_status = attendance_status

            # Mark shift as completed if all assignments are completed
            all_assignments = ShiftAssignment.objects.filter(shift=shift)
            if all(a.completion_time for a in all_assignments):
                shift.is_completed = True
                shift.completion_time = timezone.now()
                if data:
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
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    View,
):
    """
    Allows superusers and agency managers to complete a shift on behalf of a user.
    Useful in scenarios where the user cannot complete the shift themselves.
    """

    required_features = ["shift_management"]

    def get(self, request, shift_id, user_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)
        user_to_complete = get_object_or_404(
            User, id=user_id, groups__name="Agency Staff", is_active=True
        )

        # Ensure the shift belongs to the manager's agency if not superuser
        if (
            not request.user.is_superuser
            and shift.agency != request.user.profile.agency
        ):
            messages.error(request, "You cannot complete shifts outside your agency.")
            return redirect("shifts:shift_detail", pk=shift.id)

        # Ensure the worker belongs to the same agency as the shift
        if user_to_complete.profile.agency != shift.agency:
            messages.error(
                request, "The worker does not belong to the same agency as the shift."
            )
            return redirect("shifts:shift_detail", pk=shift.id)

        # Check if shift is already completed
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
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)
        user = request.user
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

        # Ensure the worker belongs to the same agency as the shift
        if user_to_complete.profile.agency != shift.agency:
            messages.error(
                request, "The worker does not belong to the same agency as the shift."
            )
            return redirect("shifts:shift_detail", pk=shift.id)

        # Check if shift is already completed
        if shift.is_completed:
            messages.info(request, "This shift has already been completed.")
            return redirect("shifts:shift_detail", pk=shift.id)

        form = ShiftCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract form data
            signature_data = form.cleaned_data.get("signature")
            latitude = form.cleaned_data.get("latitude")
            longitude = form.cleaned_data.get("longitude")
            attendance_status = form.cleaned_data.get("attendance_status")

            # Handle signature if provided
            if signature_data:
                try:
                    format, imgstr = signature_data.split(";base64,")
                    ext = format.split("/")[-1]
                    data = ContentFile(
                        base64.b64decode(imgstr),
                        name=f"shift_{shift.id}_signature_{uuid.uuid4()}.{ext}",
                    )
                except Exception as e:
                    logger.exception(
                        f"Error processing signature for Shift ID {shift.id}: {e}"
                    )
                    messages.error(request, "Invalid signature data.")
                    return redirect("shifts:shift_detail", pk=shift.id)
            else:
                data = None  # No signature provided

            # If completing on behalf, use shift's location if not superuser
            if (
                request.user.is_superuser
                or request.user.groups.filter(name="Agency Managers").exists()
            ):
                if not latitude or not longitude:
                    latitude = shift.latitude
                    longitude = shift.longitude

            # Validate geolocation proximity unless user is superuser
            if not request.user.is_superuser:
                if latitude and longitude and shift.latitude and shift.longitude:
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
                            f"You are too far from the shift location ({distance:.2f} miles).",
                        )
                        return redirect("shifts:shift_detail", pk=shift.id)
                else:
                    # If geo data is not provided, allow manual address
                    pass  # No distance check if location is not provided

            # Now, safely create or retrieve the ShiftAssignment
            assignment, created = ShiftAssignment.objects.get_or_create(
                shift=shift, worker=user_to_complete
            )

            # Update assignment with completion data
            if data:
                assignment.signature = data
            if latitude and longitude:
                assignment.completion_latitude = latitude
                assignment.completion_longitude = longitude
            assignment.completion_time = timezone.now()

            # Set attendance status if provided
            if attendance_status:
                assignment.attendance_status = attendance_status

            # Mark shift as completed if all assignments are completed
            all_assignments = ShiftAssignment.objects.filter(shift=shift)
            if all(a.completion_time for a in all_assignments):
                shift.is_completed = True
                shift.completion_time = timezone.now()
                if data:
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
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    View,
):
    """
    Handles shift completion via AJAX, returning JSON responses.
    Superusers can complete any shift without agency restrictions.
    """

    required_features = ["shift_management"]

    def post(self, request, shift_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)

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
        attendance_status = request.POST.get("attendance_status")

        # Handle signature if provided
        if signature:
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
        else:
            data = None  # No signature provided

        # Validate geolocation proximity unless user is superuser
        if not user.is_superuser:
            if latitude and longitude and shift.latitude and shift.longitude:
                try:
                    user_lat = float(latitude)
                    user_lon = float(longitude)
                    shift_lat = float(shift.latitude)
                    shift_lon = float(shift.longitude)

                    distance = haversine_distance(
                        user_lat, user_lon, shift_lat, shift_lon, unit="miles"
                    )

                except (ValueError, TypeError):
                    return JsonResponse(
                        {"success": False, "message": "Invalid location data."},
                        status=400,
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
            else:
                # If geo data is not provided, allow manual address
                pass  # No distance check if location is not provided

        # Save the signature image if provided
        if data:
            shift.signature = data

        # Mark shift as completed
        shift.is_completed = True
        shift.completion_time = timezone.now()
        if data:
            shift.signature = data

        # Update attendance status for the assignment if provided
        try:
            if not user.is_superuser:
                assignment = ShiftAssignment.objects.get(shift=shift, worker=user)
                if data:
                    assignment.signature = data
                if latitude and longitude:
                    assignment.completion_latitude = latitude
                    assignment.completion_longitude = longitude
                assignment.completion_time = timezone.now()
                if attendance_status:
                    assignment.attendance_status = attendance_status
                assignment.save()
        except ShiftAssignment.DoesNotExist:
            logger.error(
                f"ShiftAssignment does not exist for user {user.username} and shift {shift.id}."
            )
            return JsonResponse(
                {"success": False, "message": "Shift assignment not found."},
                status=404,
            )
        except Exception as e:
            logger.exception(
                f"Error updating ShiftAssignment for user {user.username} and shift {shift.id}: {e}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "An error occurred while completing the shift.",
                },
                status=500,
            )

        # Check if all assignments are completed
        all_assignments = ShiftAssignment.objects.filter(shift=shift)
        if all(a.completion_time for a in all_assignments):
            shift.is_completed = True
            shift.completion_time = timezone.now()
            if data:
                shift.signature = data
            shift.save()

        # Save shift
        try:
            shift.clean(skip_date_validation=True)
            shift.save()
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": ve.message}, status=400)

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
