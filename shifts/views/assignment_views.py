# /workspace/shiftwise/shifts/views/assignment_views.py

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from core.mixins import AgencyManagerRequiredMixin, FeatureRequiredMixin
from shifts.forms import AssignWorkerForm, UnassignWorkerForm
from shifts.models import Shift, ShiftAssignment, User

# Initialize logger
logger = logging.getLogger(__name__)


class AssignWorkerView(LoginRequiredMixin, AgencyManagerRequiredMixin, FeatureRequiredMixin, View):
    """
    Assigns a worker to a specific shift.
    Handles POST requests from the Shift Detail page.
    """

    required_features = ["shift_management"]

    def post(self, request, shift_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)

        # Extract worker ID and role from POST data
        worker_id = request.POST.get('worker')
        role = request.POST.get('role') or "Staff"  # Default role

        if not worker_id:
            messages.error(request, "Worker field is required to assign.")
            logger.warning(f"Missing worker ID in assignment by {user.username} for shift {shift.id}.")
            return redirect("shifts:shift_detail", pk=shift.id)

        worker = get_object_or_404(User, id=worker_id)

        # Initialize the AssignWorkerForm with data, shift, user, and worker
        form = AssignWorkerForm(
            data=request.POST,
            shift=shift,
            user=user,
            worker=worker,
        )

        if not form.is_valid():
            # Extract form errors
            errors = form.errors.as_text()
            messages.error(request, "Invalid form submission. " + str(form.errors))
            logger.warning(f"Invalid form data in assignment by {user.username} for shift {shift.id}. Errors: {errors}")
            return redirect("shifts:shift_detail", pk=shift.id)

        # Additional Permission Check: Ensure worker belongs to the same agency (if not superuser)
        if not user.is_superuser:
            if hasattr(worker, 'profile') and worker.profile and worker.profile.agency != shift.agency:
                messages.error(request, "You cannot assign workers from a different agency.")
                logger.warning(f"User {user.username} attempted to assign worker {worker.username} from a different agency to shift {shift.id}.")
                return redirect("shifts:shift_detail", pk=shift.id)
        # No need to check for superusers; they can assign workers from any agency

        # Check if the shift is already full using the existing 'is_full' property
        if shift.is_full:
            messages.error(request, "Cannot assign worker. The shift is already full.")
            logger.warning(f"Attempt to assign worker to full shift {shift.id} by {user.username}.")
            return redirect("shifts:shift_detail", pk=shift.id)

        # Check if the worker is already assigned to the shift
        if ShiftAssignment.objects.filter(shift=shift, worker=worker).exists():
            messages.error(
                request,
                f"Worker {worker.get_full_name()} is already assigned to this shift.",
            )
            logger.warning(
                f"Attempt to reassign worker {worker.username} to shift {shift.id} by {user.username}."
            )
            return redirect("shifts:shift_detail", pk=shift.id)

        # Validate role
        if role not in dict(ShiftAssignment.ROLE_CHOICES).keys():
            messages.error(request, "Invalid role selected.")
            logger.warning(f"Invalid role '{role}' selected by {user.username} for worker {worker.id}.")
            return redirect("shifts:shift_detail", pk=shift.id)

        # Create the ShiftAssignment
        try:
            ShiftAssignment.objects.create(
                shift=shift, worker=worker, role=role, status=ShiftAssignment.CONFIRMED
            )
            messages.success(
                request,
                f"Worker {worker.get_full_name()} has been successfully assigned to the shift with role '{role}'.",
            )
            logger.info(
                f"Worker {worker.username} assigned to shift {shift.id} with role '{role}' by {user.username}."
            )
        except ValidationError as e:
            messages.error(request, e.message)
            logger.error(f"Validation error when assigning worker: {e}")
        except Exception as e:
            messages.error(
                request,
                "An unexpected error occurred while assigning the worker.",
            )
            logger.exception(f"Unexpected error when assigning worker: {e}")

        return redirect("shifts:shift_detail", pk=shift.id)


class UnassignWorkerView(LoginRequiredMixin, AgencyManagerRequiredMixin, FeatureRequiredMixin, View):
    """
    Allows agency managers or superusers to unassign a worker from a specific shift.
    Handles POST requests from the Shift Detail page.
    """

    required_features = ["shift_management"]

    def post(self, request, shift_id, assignment_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id, is_active=True)
        assignment = get_object_or_404(ShiftAssignment, id=assignment_id, shift=shift)

        # Permission Checks
        if user.is_superuser:
            # Superusers can unassign any worker from active shifts
            pass
        elif hasattr(user, 'profile') and user.profile and user.groups.filter(name="Agency Managers").exists():
            # Agency Managers can unassign workers within their agency
            if shift.agency != user.profile.agency:
                messages.error(
                    request,
                    "You do not have permission to unassign workers from this shift.",
                )
                logger.warning(
                    f"User {user.username} attempted to unassign worker from shift {shift.id} outside their agency."
                )
                return redirect("shifts:shift_detail", pk=shift_id)
        else:
            messages.error(request, "You do not have permission to unassign shifts.")
            logger.warning(
                f"User {user.username} attempted to unassign shift {shift.id} without proper permissions."
            )
            return redirect("shifts:shift_list")

        # Perform Unassignment
        try:
            worker_full_name = assignment.worker.get_full_name()
            assignment.delete()
            messages.success(
                request, f"Worker {worker_full_name} has been unassigned from the shift."
            )
            logger.info(
                f"Worker {assignment.worker.username} unassigned from shift {shift.id} by {user.username}."
            )
        except Exception as e:
            messages.error(
                request,
                "An error occurred while unassigning the worker. Please try again.",
            )
            logger.exception(
                f"Error unassigning worker {assignment.worker.username} from shift {shift.id}: {e}"
            )
            return redirect("shifts:shift_detail", pk=shift_id)

        return redirect("shifts:shift_detail", pk=shift_id)
