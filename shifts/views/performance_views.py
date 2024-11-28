# /workspace/shiftwise/shifts/views/performance_views.py

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from core.mixins import (AgencyManagerRequiredMixin, FeatureRequiredMixin,
                         SubscriptionRequiredMixin)
from shifts.forms import StaffPerformanceForm
from shifts.models import StaffPerformance
from shiftwise.utils import generate_shift_code

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()


class StaffPerformanceListView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    ListView,
):
    """
    Displays a list of staff performances.
    Only accessible to agency managers and superusers.
    """

    required_features = ["performance_management"]
    model = StaffPerformance
    template_name = "shifts/staff_performance_list.html"
    context_object_name = "staff_performances"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = StaffPerformance.objects.all()
        else:
            agency = user.profile.agency
            queryset = StaffPerformance.objects.filter(agency=agency)

        return queryset.order_by("-created_at")


class StaffPerformanceDetailView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    DetailView,
):
    """
    Displays detailed performance metrics for a specific staff member.
    """

    required_features = ["performance_management"]
    model = StaffPerformance
    template_name = "shifts/staff_performance_detail.html"
    context_object_name = "staff_performance"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = StaffPerformance.objects.all()
        else:
            agency = user.profile.agency
            queryset = StaffPerformance.objects.filter(agency=agency)

        return queryset


class StaffPerformanceCreateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    CreateView,
):
    """
    Allows agency managers and superusers to create a new staff performance record.
    """

    required_features = ["performance_management"]
    model = StaffPerformance
    form_class = StaffPerformanceForm
    template_name = "shifts/staff_performance_form.html"
    success_url = reverse_lazy("shifts:staff_performance_list")

    def form_valid(self, form):
        performance = form.save(commit=False)
        user = self.request.user
        if not user.is_superuser:
            performance.agency = user.profile.agency
        performance.created_by = user
        performance.save()
        form.save_m2m()

        messages.success(self.request, "Staff performance record created successfully.")
        logger.info(
            f"Staff performance record '{performance}' created by {user.username}."
        )
        return super().form_valid(form)


class StaffPerformanceUpdateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    UpdateView,
):
    """
    Allows agency managers and superusers to update an existing staff performance record.
    """

    required_features = ["performance_management"]
    model = StaffPerformance
    form_class = StaffPerformanceForm
    template_name = "shifts/staff_performance_form.html"
    success_url = reverse_lazy("shifts:staff_performance_list")

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = StaffPerformance.objects.all()
        else:
            agency = user.profile.agency
            queryset = StaffPerformance.objects.filter(agency=agency)

        return queryset

    def form_valid(self, form):
        performance = form.save()
        messages.success(self.request, "Staff performance record updated successfully.")
        logger.info(
            f"Staff performance record '{performance}' updated by {self.request.user.username}."
        )
        return super().form_valid(form)


class StaffPerformanceDeleteView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    DeleteView,
):
    """
    Allows agency managers and superusers to delete a staff performance record.
    """

    required_features = ["performance_management"]
    model = StaffPerformance
    template_name = "shifts/staff_performance_confirm_delete.html"
    success_url = reverse_lazy("shifts:staff_performance_list")

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = StaffPerformance.objects.all()
        else:
            agency = user.profile.agency
            queryset = StaffPerformance.objects.filter(agency=agency)

        return queryset

    def delete(self, request, *args, **kwargs):
        performance = self.get_object()
        messages.success(request, "Staff performance record deleted successfully.")
        logger.info(
            f"Staff performance record '{performance}' deleted by {request.user.username}."
        )
        return super().delete(request, *args, **kwargs)
