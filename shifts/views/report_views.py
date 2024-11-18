# /workspace/shiftwise/shifts/views/report_views.py

import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Q, Sum
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.models import Agency
from core.mixins import (
    AgencyManagerRequiredMixin,
    FeatureRequiredMixin,
    SubscriptionRequiredMixin,
)
from shifts.models import Shift, StaffPerformance

# Initialize logger
logger = logging.getLogger(__name__)

User = get_user_model()


# ---------------------------
# Timesheet Download CBV
# ---------------------------


class TimesheetDownloadView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    FeatureRequiredMixin,
    View,
):
    """
    Generates and downloads a CSV timesheet for payroll, including total hours and total pay.
    Superusers can download timesheets for all agencies.
    Utilizes StreamingHttpResponse for efficient large file handling and robust error handling.
    """

    required_features = ["shift_management"]

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
                yield (
                    "Username",
                    "Full Name",
                    "Email",
                    "Total Shifts",
                    "Completed Shifts",
                    "Pending Shifts",
                    "Total Hours",
                    "Total Pay (£)",
                )
                for staff in staff_members:
                    yield (
                        staff.username,
                        f"{staff.first_name} {staff.last_name}",
                        staff.email,
                        staff.total_shifts or 0,
                        staff.completed_shifts or 0,
                        staff.pending_shifts or 0,
                        staff.total_hours or 0,  # Ensure no None values
                        (
                            "{0:.2f}".format(staff.total_pay)
                            if staff.total_pay
                            else "0.00"
                        ),
                    )

            # Initialize StreamingHttpResponse with a generator
            response = StreamingHttpResponse(
                (",".join(map(str, row)) + "\n" for row in csv_generator()),
                content_type="text/csv",
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

    required_features = ["shift_management"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Fetch data for the past 7 days
        dates = [timezone.now().date() - timedelta(days=i) for i in range(6, -1, -1)]
        labels = [date.strftime("%Y-%m-%d") for date in dates]

        # Filter shifts based on agency if not superuser
        if user.is_superuser:
            shifts = Shift.objects.filter(shift_date__in=dates)
            performances = StaffPerformance.objects.filter(
                shift__shift_date__gte=timezone.now().date() - timedelta(days=30)
            )
        else:
            agency = user.profile.agency
            shifts = Shift.objects.filter(shift_date__in=dates, agency=agency)
            performances = StaffPerformance.objects.filter(
                shift__shift_date__gte=timezone.now().date() - timedelta(days=30),
                agency=agency,
            )

        shift_data = [shifts.filter(shift_date=date).count() for date in dates]

        context["labels"] = labels
        context["shift_data"] = shift_data

        # Performance data
        avg_wellness = performances.aggregate(Avg("wellness_score"))[
            "wellness_score__avg"
        ] or 0
        avg_rating = performances.aggregate(Avg("performance_rating"))[
            "performance_rating__avg"
        ] or 0

        context["avg_wellness"] = round(avg_wellness, 2)
        context["avg_rating"] = round(avg_rating, 2)

        logger.debug(
            f"Report dashboard accessed by user {user.username}. Shift data: {shift_data}, Performance data: Avg Wellness: {avg_wellness}, Avg Rating: {avg_rating}"
        )

        return context