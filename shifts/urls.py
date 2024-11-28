# /workspace/shiftwise/shifts/urls.py

from django.urls import include, path

from shifts.views import (  # Staff Management Views; Shift Management Views; Shift Completion Views; Shift Booking and Unbooking Views; Timesheet and Reporting Views; Staff Performance Views; API Views; Dashboard View; Worker Assignment Views
    APIAccessView, AssignWorkerView, ReportDashboardView, ShiftBookView,
    ShiftCompleteAjaxView, ShiftCompleteForUserView, ShiftCompleteView,
    ShiftCreateView, ShiftDeleteView, ShiftDetailsAPIView, ShiftDetailView,
    ShiftListView, ShiftUnbookView, ShiftUpdateView, StaffCreateView,
    StaffDeleteView, StaffListView, StaffPerformanceCreateView,
    StaffPerformanceDeleteView, StaffPerformanceDetailView,
    StaffPerformanceListView, StaffPerformanceUpdateView, StaffUpdateView,
    TimesheetDownloadView, UnassignWorkerView)

app_name = "shifts"

urlpatterns = [
    # ---------------------------
    # Staff Management URLs
    # ---------------------------
    path("staff/", StaffListView.as_view(), name="staff_list"),
    path("staff/create/", StaffCreateView.as_view(), name="staff_create"),
    path("staff/<int:pk>/update/", StaffUpdateView.as_view(), name="staff_update"),
    path("staff/<int:pk>/delete/", StaffDeleteView.as_view(), name="staff_delete"),
    # ---------------------------
    # Shift Management URLs
    # ---------------------------
    path("", ShiftListView.as_view(), name="shift_list"),
    path("shift/<int:pk>/", ShiftDetailView.as_view(), name="shift_detail"),
    path("shift/create/", ShiftCreateView.as_view(), name="shift_create"),
    path("shift/<int:pk>/update/", ShiftUpdateView.as_view(), name="shift_update"),
    path("shift/<int:pk>/delete/", ShiftDeleteView.as_view(), name="shift_delete"),
    # ---------------------------
    # Shift Completion URLs
    # ---------------------------
    path(
        "shift/<int:shift_id>/complete/",
        ShiftCompleteView.as_view(),
        name="complete_shift",
    ),
    path(
        "shift/<int:shift_id>/complete/user/<int:user_id>/",
        ShiftCompleteForUserView.as_view(),
        name="complete_shift_for_user",
    ),
    path(
        "api/shift/<int:shift_id>/complete/",
        ShiftCompleteAjaxView.as_view(),
        name="complete_shift_ajax",
    ),
    # ---------------------------
    # Shift Booking and Unbooking URLs
    # ---------------------------
    path("shift/<int:shift_id>/book/", ShiftBookView.as_view(), name="book_shift"),
    path(
        "shift/<int:shift_id>/unbook/", ShiftUnbookView.as_view(), name="unbook_shift"
    ),
    # ---------------------------
    # Timesheet and Reporting URLs
    # ---------------------------
    path(
        "timesheet/download/",
        TimesheetDownloadView.as_view(),
        name="download_timesheet",
    ),
    path("reports/dashboard/", ReportDashboardView.as_view(), name="report_dashboard"),
    # ---------------------------
    # Staff Performance URLs
    # ---------------------------
    path(
        "performance/",
        StaffPerformanceListView.as_view(),
        name="staff_performance_list",
    ),
    path(
        "performance/<int:pk>/",
        StaffPerformanceDetailView.as_view(),
        name="staff_performance_detail",
    ),
    path(
        "performance/create/",
        StaffPerformanceCreateView.as_view(),
        name="staff_performance_create",
    ),
    path(
        "performance/<int:pk>/update/",
        StaffPerformanceUpdateView.as_view(),
        name="staff_performance_update",
    ),
    path(
        "performance/<int:pk>/delete/",
        StaffPerformanceDeleteView.as_view(),
        name="staff_performance_delete",
    ),
    # ---------------------------
    # API Access URL
    # ---------------------------
    path("api/access/", APIAccessView.as_view(), name="api_access"),
    path(
        "api/shift/<int:shift_id>/",
        ShiftDetailsAPIView.as_view(),
        name="shift_details_api",
    ),
    # ---------------------------
    # Worker Assignment URLs
    # ---------------------------
    path(
        "shift/<int:shift_id>/assign/", AssignWorkerView.as_view(), name="assign_worker"
    ),
    path(
        "shift/<int:shift_id>/unassign/<int:assignment_id>/",
        UnassignWorkerView.as_view(),
        name="unassign_worker",
    ),
]
