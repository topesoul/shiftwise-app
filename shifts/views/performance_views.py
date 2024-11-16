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

class StaffPerformanceView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    ListView
):
    """
    Displays staff performance metrics.
    """

    required_features = ['staff_performance']
    model = StaffPerformance
    template_name = 'shifts/staff_performance_list.html'
    context_object_name = 'performances'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return StaffPerformance.objects.all()
        elif user.groups.filter(name='Agency Managers').exists():
            return StaffPerformance.objects.filter(shift__agency=user.profile.agency)
        else:
            return StaffPerformance.objects.none()


class StaffPerformanceDetailView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    DetailView
):
    """
    Displays detailed information about a specific staff performance entry.
    Only accessible to superusers and agency managers associated with the performance's agency.
    """

    required_features = ['staff_performance']
    model = StaffPerformance
    template_name = 'shifts/staff_performance_detail.html'
    context_object_name = 'performance'

    def test_func(self):
        user = self.request.user
        performance = self.get_object()
        if user.is_superuser:
            return True
        elif user.groups.filter(name='Agency Managers').exists():
            return performance.shift.agency == user.profile.agency
        return False


class StaffPerformanceCreateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    CreateView
):
    model = StaffPerformance
    form_class = StaffPerformanceForm
    template_name = "shifts/create_performance.html"
    success_url = reverse_lazy("shifts:staff_performance_list")

    required_features = ['staff_performance']

    def form_valid(self, form):
        performance = form.save(commit=False)
        performance.worker = self.request.user
        performance.save()
        messages.success(self.request, "Performance data recorded successfully.")
        logger.info(f"Performance for worker {performance.worker.username} on Shift ID {performance.shift.id} recorded by {self.request.user.username}.")
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        shift_id = self.request.GET.get('shift_id')
        if shift_id:
            try:
                shift = Shift.objects.get(id=shift_id)
                initial['shift'] = shift
            except Shift.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift_id = self.request.GET.get('shift_id')
        if shift_id:
            try:
                shift = Shift.objects.get(id=shift_id)
                context['shift'] = shift
            except Shift.DoesNotExist:
                pass
        return context
class StaffPerformanceUpdateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    UpdateView
):
    model = StaffPerformance
    form_class = StaffPerformanceForm
    template_name = 'shifts/staff_performance_form.html'
    success_url = reverse_lazy('shifts:staff_performance_list')

    required_features = ['staff_performance']

    def form_valid(self, form):
        performance = form.save(commit=False)

        # Ensure the shift belongs to the manager's agency
        if not self.request.user.is_superuser:
            if performance.shift.agency != self.request.user.profile.agency:
                messages.error(self.request, "You cannot update performance for shifts outside your agency.")
                return self.form_invalid(form)

        performance.save()
        messages.success(self.request, "Staff performance updated successfully.")
        logger.info(f"Performance for worker {performance.worker.username} on Shift ID {performance.shift.id} updated by {self.request.user.username}.")
        return super().form_valid(form)


class StaffPerformanceDeleteView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    DeleteView
):
    model = StaffPerformance
    template_name = 'shifts/staff_performance_confirm_delete.html'
    success_url = reverse_lazy('shifts:staff_performance_list')

    required_features = ['staff_performance']

    def delete(self, request, *args, **kwargs):
        performance = self.get_object()
        logger.info(f"Performance for worker {performance.worker.username} on Shift ID {performance.shift.id} deleted by {request.user.username}.")
        messages.success(request, "Staff performance deleted successfully.")
        return super().delete(request, *args, **kwargs)