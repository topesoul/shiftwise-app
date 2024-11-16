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


# ---------------------------
# Timesheet Download CBV
# ---------------------------


class TimesheetDownloadView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, FeatureRequiredMixin, View
):
    """
    Generates and downloads a CSV timesheet for payroll, including total hours and total pay.
    Superusers can download timesheets for all agencies.
    Utilizes StreamingHttpResponse for efficient large file handling and robust error handling.
    """

    required_features = ['shift_management']

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
    FeatureRequiredMixin,
    TemplateView,
):
    template_name = "shifts/report_dashboard.html"

    required_features = ['shift_management']

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