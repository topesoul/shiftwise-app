# /workspace/shiftwise/shifts/views/assignment_views.py

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import FormView, View

from core.mixins import AgencyManagerRequiredMixin, FeatureRequiredMixin
from shifts.forms import AssignWorkerForm
from shifts.models import Shift, ShiftAssignment

# Initialize logger
logger = logging.getLogger(__name__)


class AssignWorkerView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, FeatureRequiredMixin, FormView
):
    """
    Assigns a worker to a specific shift.
    """

    form_class = AssignWorkerForm
    template_name = "shifts/assign_worker_form.html"

    required_features = ["shift_management"]

    def dispatch(self, request, *args, **kwargs):
        self.shift = get_object_or_404(Shift, id=self.kwargs.get("shift_id"), is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        user = self.request.user
        # Superusers can assign workers to any active shift
        if user.is_superuser:
            return True
        # Agency Managers can assign workers within their agency
        if user.groups.filter(name="Agency Managers").exists():
            return self.shift.agency == user.profile.agency
        return False

    def form_valid(self, form):
        worker = form.cleaned_data["worker"]
        shift = self.shift

        # Check if the shift is already full
        if shift.is_full:
            form.add_error(None, "Cannot assign worker. The shift is already full.")
            return self.form_invalid(form)

        # Check if the worker is already assigned to the shift
        if ShiftAssignment.objects.filter(shift=shift, worker=worker).exists():
            form.add_error(
                None, f"Worker {worker.get_full_name()} is already assigned to this shift."
            )
            return self.form_invalid(form)

        # Create the ShiftAssignment
        try:
            ShiftAssignment.objects.create(
                shift=shift, worker=worker, status=ShiftAssignment.CONFIRMED
            )
            messages.success(
                self.request,
                f"Worker {worker.get_full_name()} has been successfully assigned to the shift.",
            )
            logger.info(
                f"Worker {worker.username} assigned to shift {shift.id} by {self.request.user.username}."
            )
            return redirect("shifts:shift_detail", pk=shift.id)
        except ValidationError as e:
            form.add_error(None, e.message)
            logger.error(f"Validation error when assigning worker: {e}")
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(
                None, "An unexpected error occurred while assigning the worker."
            )
            logger.exception(f"Unexpected error when assigning worker: {e}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("shifts:shift_detail", kwargs={"pk": self.shift.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shift"] = self.shift
        return context


class UnassignWorkerView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, FeatureRequiredMixin, View
):
    """
    Allows agency managers or superusers to unassign a worker from a specific shift.
    Superusers can unassign any worker, while agency managers can unassign workers within their agency.
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
        elif user.groups.filter(name="Agency Managers").exists():
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
                f"Worker {worker_full_name} unassigned from shift {shift.id} by {user.username}."
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