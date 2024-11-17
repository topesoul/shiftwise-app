# /workspace/shiftwise/shifts/views/staff_views.py

import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Count, ExpressionWrapper, FloatField, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from accounts.forms import StaffCreationForm, StaffUpdateForm
from accounts.models import Profile
from core.mixins import (
    AgencyManagerRequiredMixin,
    FeatureRequiredMixin,
    SubscriptionRequiredMixin,
)
from shifts.models import Shift, ShiftAssignment, StaffPerformance
from shifts.utils import is_shift_full, is_user_assigned

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()


class StaffListView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    ListView,
):
    """
    Displays a list of staff members.
    Only accessible to users with 'custom_integrations' feature.
    """

    required_features = ["custom_integrations"]
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
    FeatureRequiredMixin,
    CreateView,
):
    """
    Allows agency managers and superusers to add new staff members to their agency.
    Superusers can add staff without being associated with any agency.
    """

    required_features = ["custom_integrations"]
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
    FeatureRequiredMixin,
    UpdateView,
):
    """
    Allows agency managers or superusers to edit staff details.
    Superusers can edit any staff member regardless of agency association.
    """

    required_features = ["custom_integrations"]
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
    FeatureRequiredMixin,
    DeleteView,
):
    """
    Allows agency managers or superusers to deactivate a staff member.
    Superusers can deactivate any staff member regardless of agency association.
    """

    required_features = ["custom_integrations"]
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
            f"Staff member {staff_member.username} deactivated by user {request.user.username}."
        )
        return redirect(self.success_url)
