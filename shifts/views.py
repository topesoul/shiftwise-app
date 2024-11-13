# /workspace/shiftwise/shifts/views.py

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
from accounts.models import Notification, Profile, Agency
from accounts.forms import StaffCreationForm, StaffUpdateForm
from .models import Shift, ShiftAssignment, StaffPerformance
from .forms import ShiftForm, ShiftCompletionForm, StaffPerformanceForm, AssignWorkerForm, UnassignWorkerForm
from .filters import ShiftFilter
from .utils import is_shift_full, is_user_assigned
from core.mixins import AgencyOwnerRequiredMixin, SubscriptionRequiredMixin, AgencyManagerRequiredMixin, AgencyStaffRequiredMixin, FeatureRequiredMixin
from shiftwise.utils import haversine_distance, predict_staffing_needs, generate_shift_code

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()


# Utility Functions
def is_agency_manager(user):
    """Check if the user is an agency manager or a superuser."""
    return user.is_superuser or user.groups.filter(name="Agency Managers").exists()


def is_agency_staff(user):
    """Check if the user is agency staff or a superuser."""
    return user.is_superuser or user.groups.filter(name="Agency Staff").exists()


# Custom Permission Denied and Error Views
def custom_permission_denied_view(request, exception):
    """
    Render a custom 403 Forbidden page.
    """
    return render(request, "403.html", status=403)


def custom_page_not_found_view(request, exception):
    """
    Render a custom 404 Not Found page.
    """
    return render(request, "404.html", status=404)


def custom_server_error_view(request):
    """
    Render a custom 500 Server Error page.
    """
    return render(request, "500.html", status=500)


# ---------------------------
# Staff Management CBVs
# ---------------------------


class StaffListView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    ListView,
):
    """
    Displays a list of staff members.
    Only accessible to users with 'notifications_enabled' feature (Enterprise Plan).
    """

    required_features = ["notifications_enabled"]
    model = User
    template_name = "shifts/staff_list.html"
    context_object_name = "staff_members"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        agency = user.profile.agency if not user.is_superuser else None
        search_query = self.request.GET.get("search", "")
        status_filter = self.request.GET.get("status", "")
        date_from = self.request.GET.get("date_from", "")
        date_to = self.request.GET.get("date_to", "")

        # Base queryset filtering Agency Staff and active users
        staff_members = User.objects.filter(groups__name="Agency Staff", is_active=True)

        if not user.is_superuser:
            staff_members = staff_members.filter(profile__agency=agency)

        # Annotate with shift statistics
        staff_members = staff_members.annotate(
            total_shifts=Count("shift_assignments"),
            completed_shifts=Count(
                "shift_assignments",
                filter=Q(shift_assignments__shift__status=Shift.STATUS_COMPLETED),
            ),
            pending_shifts=Count(
                "shift_assignments",
                filter=Q(shift_assignments__shift__status=Shift.STATUS_PENDING),
            ),
            total_hours=Sum(
                "shift_assignments__shift__duration",
                filter=Q(shift_assignments__shift__status=Shift.STATUS_COMPLETED),
            ),
            total_pay=Sum(
                ExpressionWrapper(
                    F("shift_assignments__shift__duration")
                    * F("shift_assignments__shift__hourly_rate"),
                    output_field=FloatField(),
                ),
                filter=Q(shift_assignments__shift__status=Shift.STATUS_COMPLETED),
            ),
        )

        # Apply search filter
        if search_query:
            staff_members = staff_members.filter(
                Q(username__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        # Apply shift status filter
        if status_filter:
            staff_members = staff_members.filter(
                shift_assignments__shift__status=status_filter,
            ).distinct()

        # Apply date range filter
        if date_from and date_to:
            staff_members = staff_members.filter(
                shift_assignments__shift__shift_date__range=[date_from, date_to]
            ).distinct()

        # Order the queryset by username
        staff_members = staff_members.order_by("username")

        return staff_members

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["status_filter"] = self.request.GET.get("status", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")
        return context


class StaffCreateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    CreateView,
):
    """
    Allows agency managers and superusers to add new staff members to their agency.
    Superusers can add staff without being associated with any agency.
    """

    model = User
    form_class = StaffCreationForm
    template_name = "shifts/add_staff.html"
    success_url = reverse_lazy("shifts:staff_list")

    def form_valid(self, form):
        user = form.save(commit=False)
        if not self.request.user.is_superuser:
            agency = self.request.user.profile.agency
            if not agency:
                messages.error(self.request, "You are not associated with any agency.")
                logger.warning(
                    f"User {self.request.user.username} attempted to add staff without an associated agency."
                )
                return redirect("accounts:profile")
            user.save()
            user.profile.agency = agency
            user.profile.save()
        else:
            user.save()
        # Add to 'Agency Staff' group
        agency_staff_group, created = Group.objects.get_or_create(name="Agency Staff")
        user.groups.add(agency_staff_group)
        messages.success(self.request, "Staff member added successfully.")
        logger.info(
            f"Staff member {user.username} added by {self.request.user.username}."
        )
        return super().form_valid(form)


class StaffUpdateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    UpdateView,
):
    """
    Allows agency managers or superusers to edit staff details.
    Superusers can edit any staff member regardless of agency association.
    """

    model = User
    form_class = StaffUpdateForm
    template_name = "shifts/edit_staff.html"
    success_url = reverse_lazy("shifts:staff_list")

    def dispatch(self, request, *args, **kwargs):
        """
        Ensure that non-superusers can only edit staff within their agency.
        """
        user = self.request.user
        staff_member = self.get_object()
        if not user.is_superuser and staff_member.profile.agency != user.profile.agency:
            messages.error(
                request, "You do not have permission to edit this staff member."
            )
            return redirect("shifts:staff_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "Staff details updated successfully.")
        logger.info(
            f"Staff member {user.username} updated by {self.request.user.username}."
        )
        return super().form_valid(form)


class StaffDeleteView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    DeleteView,
):
    """
    Allows agency managers or superusers to deactivate a staff member.
    Superusers can deactivate any staff member regardless of agency association.
    """

    model = User
    template_name = "shifts/delete_staff.html"
    success_url = reverse_lazy("shifts:staff_list")

    def dispatch(self, request, *args, **kwargs):
        """
        Ensure that non-superusers can only deactivate staff within their agency.
        """
        user = self.request.user
        staff_member = self.get_object()
        if not user.is_superuser and staff_member.profile.agency != user.profile.agency:
            messages.error(
                request, "You do not have permission to deactivate this staff member."
            )
            return redirect("shifts:staff_list")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        staff_member = self.get_object()
        staff_member.is_active = False
        staff_member.save()
        messages.success(request, "Staff member deactivated successfully.")
        logger.info(
            f"Staff member {staff_member.username} deactivated by {request.user.username}."
        )
        return redirect(self.success_url)


# ---------------------------
# Shift Management CBVs
# ---------------------------


class ShiftListView(LoginRequiredMixin, AgencyManagerRequiredMixin, AgencyOwnerRequiredMixin, SubscriptionRequiredMixin, ListView):
    """
    Displays a list of shifts available to the user with search and filter capabilities.
    Includes distance calculations based on user's registered address.
    Superusers see all shifts without agency restrictions.
    """

    model = Shift
    template_name = "shifts/shift_list.html"
    context_object_name = "shifts"
    paginate_by = 10

    required_features = ['shift_management']

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
        elif (
            user.groups.filter(name="Agency Managers").exists()
            or user.groups.filter(name="Agency Staff").exists()
        ):
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
    CreateView,
):
    """
    Allows agency managers and superusers to create new shifts.
    Superusers can assign shifts to any agency or without an agency.
    """

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
            # Superuser must assign an agency
            agency = form.cleaned_data.get("agency")
            if not agency:
                form.add_error("agency", "Agency is required for creating a shift.")
                return self.form_invalid(form)
            shift.agency = agency
        else:
            # Agency managers assign shifts to their own agency
            agency = self.request.user.profile.agency
            if not agency:
                messages.error(self.request, "You are not associated with any agency.")
                logger.warning(
                    f"User {self.request.user.username} attempted to create shift without an associated agency."
                )
                return redirect("accounts:profile")
            shift.agency = agency

        # Optionally, generate a unique shift code
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
    UpdateView,
):
    """
    Allows agency managers and superusers to update existing shifts.
    Superusers can change the agency of a shift or leave it without an agency.
    """

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
            # Superuser can change the agency if needed
            agency = form.cleaned_data.get("agency")
            if not agency:
                form.add_error("agency", "Agency is required for updating a shift.")
                return self.form_invalid(form)
            shift.agency = agency
        else:
            # Agency managers cannot change the agency of a shift
            shift.agency = self.request.user.profile.agency

        # Optionally, re-generate shift code if needed
        # shift.shift_code = generate_shift_code()

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
    DeleteView,
):
    """
    Allows agency managers and superusers to delete shifts.
    Superusers can delete any shift regardless of agency association.
    """

    model = Shift
    template_name = "shifts/shift_confirm_delete.html"
    success_url = reverse_lazy("shifts:shift_list")

    def delete(self, request, *args, **kwargs):
        shift = self.get_object()
        logger.info(f"Shift '{shift.name}' deleted by {request.user.username}.")
        messages.success(request, "Shift deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ---------------------------
# Shift Completion CBVs
# ---------------------------


class ShiftCompleteView(
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, View
):
    """
    Allows agency staff or superusers to complete a shift with digital signature and location verification.
    Superusers can complete any shift without agency restrictions.
    """

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
    LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, View
):
    """
    Allows superusers and agency managers to complete a shift on behalf of a user.
    Useful in scenarios where the user cannot complete the shift themselves.
    """

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
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, View
):
    """
    Handles shift completion via AJAX, returning JSON responses.
    Superusers can complete any shift without agency restrictions.
    """

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
            assignment.attendance_status = attendance_status  # Update attendance status
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


# ---------------------------
# Shift Booking and Unbooking CBVs
# ---------------------------


class ShiftBookView(
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, View
):
    """
    Allows agency staff or superusers to book a shift based on availability and proximity.
    Superusers can book any shift without agency restrictions.
    """

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
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, View
):
    """
    Allows agency staff or superusers to unbook a shift.
    Superusers can unbook any shift without agency restrictions.
    """

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


# ---------------------------
# Timesheet Download CBV
# ---------------------------


class TimesheetDownloadView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, View
):
    """
    Generates and downloads a CSV timesheet for payroll, including total hours and total pay.
    Superusers can download timesheets for all agencies.
    Utilizes StreamingHttpResponse for efficient large file handling and robust error handling.
    """
    def get(self, request, *args, **kwargs):
        try:
            agency = (
                request.user.profile.agency if not request.user.is_superuser else None
            )
            if not request.user.is_superuser and not agency:
                messages.error(request, "You are not associated with any agency.")
                logger.error(
                    f"User {request.user.username} attempted to download timesheet without an associated agency."
                )
                raise PermissionDenied  # Return a 403 Forbidden response

            # Retrieve filter parameters
            search_query = request.GET.get("search", "")
            status_filter = request.GET.get("status", "")
            date_from = request.GET.get("date_from", "")
            date_to = request.GET.get("date_to", "")

            # Base queryset filtering Agency Staff and active users
            staff_members = User.objects.filter(
                groups__name="Agency Staff", is_active=True
            )

            if not request.user.is_superuser:
                staff_members = staff_members.filter(profile__agency=agency)

            # Annotate with shift statistics
            staff_members = staff_members.annotate(
                total_shifts=Count("shift_assignments"),
                completed_shifts=Count(
                    "shift_assignments",
                    filter=Q(shift_assignments__shift__status=Shift.STATUS_COMPLETED),
                ),
                pending_shifts=Count(
                    "shift_assignments",
                    filter=Q(shift_assignments__shift__status=Shift.STATUS_PENDING),
                ),
                total_hours=Sum(
                    "shift_assignments__shift__duration",
                    filter=Q(shift_assignments__shift__status=Shift.STATUS_COMPLETED),
                ),
                total_pay=Sum(
                    ExpressionWrapper(
                        F("shift_assignments__shift__duration")
                        * F("shift_assignments__shift__hourly_rate"),
                        output_field=FloatField(),
                    ),
                    filter=Q(shift_assignments__shift__status=Shift.STATUS_COMPLETED),
                ),
            )

            # Apply search filter
            if search_query:
                staff_members = staff_members.filter(
                    Q(username__icontains=search_query)
                    | Q(first_name__icontains=search_query)
                    | Q(last_name__icontains=search_query)
                    | Q(email__icontains=search_query)
                )

            # Apply shift status filter
            if status_filter:
                staff_members = staff_members.filter(
                    shift_assignments__shift__status=status_filter
                ).distinct()

            # Apply date range filter
            if date_from and date_to:
                staff_members = staff_members.filter(
                    shift_assignments__shift__shift_date__range=[date_from, date_to]
                ).distinct()

            # Define a generator to stream CSV rows
            def csv_generator():
                yield [
                    "Username",
                    "Full Name",
                    "Email",
                    "Total Shifts",
                    "Completed Shifts",
                    "Pending Shifts",
                    "Total Hours",
                    "Total Pay (£)",
                ]
                for staff in staff_members:
                    yield [
                        staff.username,
                        f"{staff.first_name} {staff.last_name}",
                        staff.email,
                        staff.total_shifts,
                        staff.completed_shifts,
                        staff.pending_shifts,
                        staff.total_hours or 0,  # Ensure no None values
                        (
                            "{0:.2f}".format(staff.total_pay)
                            if staff.total_pay
                            else "0.00"
                        ),
                    ]

            # Initialize StreamingHttpResponse with a generator
            response = StreamingHttpResponse(
                (row for row in csv_generator()), content_type="text/csv"
            )
            filename = f"timesheet_{timezone.now().strftime('%Y%m%d')}.csv"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            logger.info(
                f"Timesheet downloaded by user {request.user.username} for agency {agency.name if agency else 'All Agencies'}."
            )
            return response

        except PermissionDenied:
            logger.warning(
                f"User {request.user.username} attempted unauthorized access to TimesheetDownloadView."
            )
            return render(request, "403.html", status=403)
        except Exception as e:
            logger.exception(f"Error in TimesheetDownloadView: {e}")
            messages.error(
                request,
                "An error occurred while downloading the timesheet. Please try again later.",
            )
            return redirect("shifts:staff_list")


# ---------------------------
# Report Dashboard View
# ---------------------------


class ReportDashboardView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    TemplateView,
):
    template_name = "shifts/report_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Existing shift data
        from datetime import datetime, timedelta

        dates = [datetime.now() - timedelta(days=i) for i in range(7)]
        labels = [date.strftime("%Y-%m-%d") for date in dates]
        shift_data = [
            Shift.objects.filter(shift_date=date.date()).count() for date in dates
        ]
        context["labels"] = labels[::-1]
        context["shift_data"] = shift_data[::-1]

        # Performance data
        performance = StaffPerformance.objects.filter(
            shift__shift_date__gte=datetime.now() - timedelta(days=30)
        )
        avg_wellness = (
            performance.aggregate(models.Avg("wellness_score"))["wellness_score__avg"]
            or 0
        )
        avg_rating = (
            performance.aggregate(models.Avg("performance_rating"))[
                "performance_rating__avg"
            ]
            or 0
        )
        context["avg_wellness"] = round(avg_wellness, 2)
        context["avg_rating"] = round(avg_rating, 2)
        return context


# ---------------------------
# Staff Performance CBVs
# ---------------------------


class StaffPerformanceView(LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, ListView):
    """
    Displays staff performance metrics.
    """
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


class StaffPerformanceDetailView(LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, DetailView):
    """
    Displays detailed information about a specific staff performance entry.
    Only accessible to superusers and agency managers associated with the performance's agency.
    """
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
    CreateView,
):
    model = StaffPerformance
    form_class = StaffPerformanceForm
    template_name = "shifts/create_performance.html"
    success_url = reverse_lazy("shifts:staff_performance_list")

    def form_valid(self, form):
        performance = form.save(commit=False)
        performance.worker = self.request.user
        performance.save()
        messages.success(self.request, "Performance data recorded successfully.")
        logger.info(f"Performance for worker {performance.worker.username} on Shift ID {performance.shift.id} recorded by {self.request.user.username}.")
        return super().form_valid(form)


class StaffPerformanceUpdateView(LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, UpdateView):
    model = StaffPerformance
    form_class = StaffPerformanceForm
    template_name = 'shifts/staff_performance_form.html'
    success_url = reverse_lazy('shifts:staff_performance_list')

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


class StaffPerformanceDeleteView(LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, DeleteView):
    model = StaffPerformance
    template_name = 'shifts/staff_performance_confirm_delete.html'
    success_url = reverse_lazy('shifts:staff_performance_list')

    def delete(self, request, *args, **kwargs):
        performance = self.get_object()
        logger.info(f"Performance for worker {performance.worker.username} on Shift ID {performance.shift.id} deleted by {request.user.username}.")
        messages.success(request, "Staff performance deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ---------------------------
# Shift Details API View
# ---------------------------


class ShiftDetailsAPIView(LoginRequiredMixin, View):
    """
    Provides shift details in JSON format.
    """
    def get(self, request, shift_id, *args, **kwargs):
        shift = get_object_or_404(Shift, id=shift_id)
        shift_data = {
            'id': shift.id,
            'name': shift.name,
            'shift_date': shift.shift_date,
            'start_time': shift.start_time,
            'end_time': shift.end_time,
            'status': shift.status,
            'capacity': shift.capacity,
            'available_slots': shift.available_slots,
            'is_full': shift.is_full,
            'agency': shift.agency.name if shift.agency else 'No Agency',
            'latitude': shift.latitude,
            'longitude': shift.longitude,
        }
        return JsonResponse({'shift': shift_data})


# ---------------------------
# Notification Views
# ---------------------------


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'shifts/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return self.request.user.notifications.filter(read=False).order_by('-created_at')


class MarkNotificationReadView(LoginRequiredMixin, View):
    """
    Marks a notification as read.
    """
    @method_decorator(csrf_protect, name='dispatch')
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.read = True
        notification.save()
        logger.info(f"Notification ID {notification.id} marked as read by {request.user.username}.")
        return JsonResponse({'success': True})


# ---------------------------
# Dashboard View
# ---------------------------


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'shifts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Fetch shifts based on user role
        if user.is_superuser:
            shifts = Shift.objects.all()
        elif user.groups.filter(name='Agency Managers').exists():
            shifts = Shift.objects.filter(agency=user.profile.agency)
        elif user.groups.filter(name='Agency Staff').exists():
            shifts = Shift.objects.filter(assignments__worker=user)
        else:
            shifts = Shift.objects.none()

        context['shifts'] = shifts

        # Fetch notifications
        context['notifications'] = user.notifications.filter(read=False).order_by('-created_at')

        return context


class AssignWorkerView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    form_class = AssignWorkerForm
    template_name = "shifts/assign_worker_form.html"

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
        if is_shift_full(shift):
            messages.error(self.request, "Cannot assign worker. The shift is already full.")
            return self.form_invalid(form)

        # Check if the worker is already assigned to the shift
        if is_user_assigned(shift, worker):
            messages.info(self.request, f"{worker.username} is already assigned to this shift.")
            return self.form_invalid(form)

        # Create the ShiftAssignment
        ShiftAssignment.objects.create(shift=shift, worker=worker)
        messages.success(self.request, f"Worker {worker.username} has been assigned to the shift.")
        logger.info(f"Worker {worker.username} assigned to shift {shift.id} by {self.request.user.username}.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('shifts:shift_detail', kwargs={'pk': self.shift.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shift'] = self.shift
        return context


class UnassignWorkerView(LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, View):
    """
    Allows agency managers or superusers to unassign a worker from a specific shift.
    Superusers can unassign any worker, while agency managers can unassign workers within their agency.
    """

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
            assignment.delete()
            messages.success(request, f"Worker {assignment.worker.get_full_name()} has been unassigned from the shift.")
            logger.info(f"Worker {assignment.worker.username} unassigned from shift {shift.id} by {user.username}.")
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