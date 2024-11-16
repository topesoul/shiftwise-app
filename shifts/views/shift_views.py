# /workspace/shiftwise/shifts/views/shift_views.py

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
from shiftwise.utils import haversine_distance, generate_shift_code

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()

class ShiftListView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    ListView
):
    """
    Displays a list of shifts available to the user with search and filter capabilities.
    Includes distance calculations based on user's registered address.
    Superusers see all shifts without agency restrictions.
    """

    required_features = ['shift_management']
    model = Shift
    template_name = "shifts/shift_list.html"
    context_object_name = "shifts"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        profile = user.profile
        queryset = Shift.objects.all().order_by("shift_date", "start_time")

        # Filter based on user role
        if user.is_superuser:
            pass  # Superusers see all shifts
        elif user.groups.filter(name="Agency Managers").exists():
            queryset = queryset.filter(agency=profile.agency)
        elif user.groups.filter(name="Agency Staff").exists():
            queryset = queryset.filter(agency=profile.agency)
        else:
            queryset = Shift.objects.none()

        # Apply search filters through ShiftFilter
        self.filterset = ShiftFilter(self.request.GET, queryset=queryset)
        queryset = self.filterset.qs

        # Prefetch related assignments and workers for optimization
        queryset = queryset.prefetch_related("assignments__worker")

        # Calculate distance and annotate
        if profile.latitude and profile.longitude:
            shifts_with_distance = []
            for shift in queryset:
                if shift.latitude and shift.longitude:
                    distance = haversine_distance(
                        profile.latitude,
                        profile.longitude,
                        shift.latitude,
                        shift.longitude,
                        unit="miles",
                    )
                    shift.distance_to_user = distance
                else:
                    shift.distance_to_user = None
                shifts_with_distance.append(shift)
            return shifts_with_distance
        else:
            # If user has no registered address, show all shifts
            for shift in queryset:
                shift.distance_to_user = None
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset
        return context


class ShiftDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Displays details of a specific shift, including distance from the user's location.
    Superusers can view any shift regardless of agency association.
    """

    model = Shift
    template_name = "shifts/shift_detail.html"
    context_object_name = "shift"

    def test_func(self):
        user = self.request.user
        shift = self.get_object()
        if user.is_superuser:
            return True
        elif user.groups.filter(name="Agency Managers").exists() or user.groups.filter(name="Agency Staff").exists():
            return shift.agency == user.profile.agency
        return False

    def get_queryset(self):
        user = self.request.user
        queryset = Shift.objects.select_related("agency").prefetch_related(
            "assignments__worker"
        )

        if user.is_superuser:
            return queryset
        elif user.groups.filter(name="Agency Managers").exists():
            return queryset.filter(agency=user.profile.agency)
        elif user.groups.filter(name="Agency Staff").exists():
            return queryset.filter(agency=user.profile.agency)
        else:
            return Shift.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift = self.object
        user = self.request.user
        profile = user.profile

        # Calculate distance if user has a registered address and shift has coordinates
        distance = None
        if (
            profile.latitude
            and profile.longitude
            and shift.latitude
            and shift.longitude
        ):
            distance = haversine_distance(
                profile.latitude,
                profile.longitude,
                shift.latitude,
                shift.longitude,
                unit="miles",
            )

        context["distance_to_shift"] = distance
        context["is_assigned"] = shift.assignments.filter(worker=user).exists()
        context["can_book"] = (
            user.groups.filter(name="Agency Staff").exists()
            and not shift.is_full
            and not context["is_assigned"]
        )
        context["can_unbook"] = (
            user.groups.filter(name="Agency Staff").exists() and context["is_assigned"]
        )
        context["can_edit"] = user.is_superuser or (
            user.groups.filter(name="Agency Managers").exists()
            and shift.agency == profile.agency
        )
        context["assigned_workers"] = shift.assignments.all()
        context["can_assign_workers"] = (
            user.is_superuser or user.groups.filter(name="Agency Managers").exists()
        )

        # For assigning workers
        if context["can_assign_workers"]:
            if user.is_superuser:
                available_workers = User.objects.filter(
                    groups__name="Agency Staff", is_active=True
                ).exclude(shift_assignments__shift=shift)
            else:
                available_workers = User.objects.filter(
                    profile__agency=shift.agency,
                    groups__name="Agency Staff",
                    is_active=True,
                ).exclude(shift_assignments__shift=shift)
            context["available_workers"] = available_workers

        return context


class ShiftCreateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    CreateView,
):
    """
    Allows agency managers and superusers to create new shifts.
    Superusers can assign shifts to any agency or without an agency.
    """

    required_features = ['shift_management']
    model = Shift
    form_class = ShiftForm
    template_name = "shifts/shift_form.html"
    success_url = reverse_lazy("shifts:shift_list")

    def dispatch(self, request, *args, **kwargs):
        """
        Ensure that non-superusers have an associated agency before creating a shift.
        """
        if not request.user.is_superuser:
            if not hasattr(request.user, 'profile') or not request.user.profile.agency:
                messages.error(request, "You are not associated with any agency.")
                logger.warning(
                    f"User {request.user.username} attempted to create shift without an associated agency."
                )
                return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Pass the user instance to the form to handle conditional fields.
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        shift = form.save(commit=False)
        if self.request.user.is_superuser:
            # Superuser must assign an agency
            agency = form.cleaned_data.get("agency")
            if not agency:
                form.add_error("agency", "Agency is required for creating a shift.")
                return self.form_invalid(form)
            shift.agency = agency
        else:
            # Agency managers assign shifts to their own agency
            agency = self.request.user.profile.agency
            shift.agency = agency

            # Check shift limit
            subscription = agency.subscription
            if subscription and subscription.plan.shift_limit is not None:
                # Count shifts created this month
                current_time = timezone.now()
                current_month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                current_shift_count = Shift.objects.filter(
                    agency=shift.agency,
                    shift_date__gte=current_month_start
                ).count()
                if current_shift_count >= subscription.plan.shift_limit:
                    messages.error(
                        self.request,
                        f"Your agency has reached the maximum number of shifts ({subscription.plan.shift_limit}) for this month. Please upgrade your subscription."
                    )
                    logger.info(
                        f"Agency '{shift.agency.name}' has reached the shift limit for the month."
                    )
                    return redirect("subscriptions:upgrade_subscription")  # Redirect to upgrade page

        # Generate a unique shift code
        shift.shift_code = generate_shift_code()

        # Save the shift
        shift.save()
        form.save_m2m()

        messages.success(self.request, "Shift created successfully.")
        logger.info(
            f"Shift '{shift.name}' created by {self.request.user.username} for agency {agency.name if agency else 'No Agency'}."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["GOOGLE_PLACES_API_KEY"] = settings.GOOGLE_PLACES_API_KEY
        return context


class ShiftUpdateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    UpdateView,
):
    """
    Allows agency managers and superusers to update existing shifts.
    Superusers can change the agency of a shift or leave it without an agency.
    """

    required_features = ['shift_management']
    model = Shift
    form_class = ShiftForm
    template_name = "shifts/shift_form.html"
    success_url = reverse_lazy("shifts:shift_list")

    def get_form_kwargs(self):
        """
        Pass the user instance to the form to handle conditional fields.
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        shift = form.save(commit=False)
        if self.request.user.is_superuser:
            # Superuser can change the agency
            agency = form.cleaned_data.get("agency")
            if not agency:
                form.add_error("agency", "Agency is required for updating a shift.")
                return self.form_invalid(form)
            shift.agency = agency
        else:
            # Agency managers cannot change the agency of a shift
            shift.agency = self.request.user.profile.agency

        shift.shift_code = generate_shift_code()

        # Save the shift
        shift.save()
        form.save_m2m()

        messages.success(self.request, "Shift updated successfully.")
        logger.info(f"Shift '{shift.name}' updated by {self.request.user.username}.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Handle invalid form submissions.
        """
        messages.error(
            self.request,
            "There was an error updating the shift. Please correct the errors below.",
        )
        return super().form_invalid(form)


class ShiftDeleteView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    DeleteView,
):
    """
    Allows agency managers and superusers to delete shifts.
    Superusers can delete any shift regardless of agency association.
    """

    required_features = ['shift_management']
    model = Shift
    template_name = "shifts/shift_confirm_delete.html"
    success_url = reverse_lazy("shifts:shift_list")

    def delete(self, request, *args, **kwargs):
        shift = self.get_object()
        logger.info(f"Shift '{shift.name}' deleted by {request.user.username}.")
        messages.success(request, "Shift deleted successfully.")
        return super().delete(request, *args, **kwargs)