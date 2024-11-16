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


class AssignWorkerView(LoginRequiredMixin, AgencyManagerRequiredMixin, FeatureRequiredMixin, FormView):
    """
    Assigns a worker to a specific shift.
    """
    form_class = AssignWorkerForm
    template_name = "shifts/assign_worker_form.html"

    required_features = ['shift_management']

    def dispatch(self, request, *args, **kwargs):
        self.shift = get_object_or_404(Shift, id=self.kwargs.get('shift_id'))
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        user = self.request.user
        # Superusers can assign workers to any shift
        if user.is_superuser:
            return True
        # Agency Managers can assign workers within their agency
        if user.groups.filter(name="Agency Managers").exists():
            return self.shift.agency == user.profile.agency
        return False

    def form_valid(self, form):
        worker = form.cleaned_data['worker']
        shift = self.shift

        # Check if the shift is already full
        if shift.is_full:
            form.add_error(None, "Cannot assign worker. The shift is already full.")
            return self.form_invalid(form)

        # Check if the worker is already assigned to the shift
        if ShiftAssignment.objects.filter(shift=shift, worker=worker).exists():
            form.add_error(None, f"Worker {worker.username} is already assigned to this shift.")
            return self.form_invalid(form)

        # Create the ShiftAssignment
        try:
            ShiftAssignment.objects.create(shift=shift, worker=worker, status=ShiftAssignment.CONFIRMED)
            messages.success(self.request, f"Worker {worker.username} has been successfully assigned to the shift.")
            logger.info(f"Worker {worker.username} assigned to shift {shift.id} by {self.request.user.username}.")
            return redirect('shifts:shift_detail', pk=shift.id)
        except ValidationError as e:
            form.add_error(None, e.message)
            logger.error(f"Validation error when assigning worker: {e}")
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, "An unexpected error occurred while assigning the worker.")
            logger.exception(f"Unexpected error when assigning worker: {e}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('shifts:shift_detail', kwargs={'pk': self.shift.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shift'] = self.shift
        return context


class UnassignWorkerView(LoginRequiredMixin, AgencyManagerRequiredMixin, FeatureRequiredMixin, View):
    """
    Allows agency managers or superusers to unassign a worker from a specific shift.
    Superusers can unassign any worker, while agency managers can unassign workers within their agency.
    """

    required_features = ['shift_management']

    def post(self, request, shift_id, assignment_id, *args, **kwargs):
        user = request.user
        shift = get_object_or_404(Shift, id=shift_id)
        assignment = get_object_or_404(ShiftAssignment, id=assignment_id, shift=shift)

        # Permission Checks
        if user.is_superuser:
            # Superusers can unassign any worker
            pass
        elif user.groups.filter(name="Agency Managers").exists():
            # Agency Managers can unassign workers within their agency
            if shift.agency != user.profile.agency:
                messages.error(request, "You do not have permission to unassign workers from this shift.")
                logger.warning(
                    f"User {user.username} attempted to unassign worker from shift {shift.id} outside their agency."
                )
                return redirect("shifts:shift_detail", pk=shift_id)
        elif user.groups.filter(name="Agency Staff").exists():
            # Agency Staff can only unassign themselves
            if assignment.worker != user:
                messages.error(request, "You do not have permission to unassign this worker.")
                logger.warning(
                    f"User {user.username} attempted to unassign worker {assignment.worker.username} from shift {shift.id}."
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
            worker_username = assignment.worker.username
            assignment.delete()
            messages.success(request, f"Worker {worker_username} has been unassigned from the shift.")
            logger.info(f"Worker {worker_username} unassigned from shift {shift.id} by {user.username}.")
        except Exception as e:
            messages.error(request, "An error occurred while unassigning the worker. Please try again.")
            logger.exception(f"Error unassigning worker {assignment.worker.username} from shift {shift.id}: {e}")
            return redirect("shifts:shift_detail", pk=shift_id)

        return redirect("shifts:shift_detail", pk=shift_id)

    def get(self, request, shift_id, assignment_id, *args, **kwargs):
        """
        Redirect GET requests to the shift detail page.
        """
        return redirect("shifts:shift_detail", pk=shift_id)