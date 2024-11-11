# /workspace/shiftwise/shifts/urls.py

from django.urls import path
from . import views

app_name = "shifts"

urlpatterns = [
    # ---------------------------
    # Shift List and Detail Views
    # ---------------------------
    
    path(
        "",
        views.ShiftListView.as_view(),
        name="shift_list"
    ),
    path(
        "shift/<int:pk>/",
        views.ShiftDetailView.as_view(),
        name="shift_detail"
    ),
    
    # ---------------------------
    # Shift CRUD Operations
    # ---------------------------
    
    path(
        "shift/create/",
        views.ShiftCreateView.as_view(),
        name="shift_create"
    ),
    path(
        "shift/<int:pk>/update/",
        views.ShiftUpdateView.as_view(),
        name="shift_update"
    ),
    path(
        "shift/<int:pk>/delete/",
        views.ShiftDeleteView.as_view(),
        name="shift_delete"
    ),
    
    # ---------------------------
    # Shift Assignment and Unassignment
    # ---------------------------
    
    path(
        "shift/<int:shift_id>/assign_worker/",
        views.AssignWorkerView.as_view(),
        name="assign_worker"
    ),
    path(
        "shift/<int:shift_id>/unassign_worker/<int:worker_id>/",
        views.UnassignWorkerView.as_view(),
        name="unassign_worker"
    ),
    
    # ---------------------------
    # Shift Completion
    # ---------------------------
    
    path(
        "shift/<int:shift_id>/complete/",
        views.ShiftCompleteView.as_view(),
        name="shift_complete"
    ),
    path(
        "shift/<int:shift_id>/complete/<int:user_id>/",
        views.ShiftCompleteForUserView.as_view(),
        name="shift_complete_for_user"
    ),
    path(
        "shift/<int:shift_id>/complete_ajax/",
        views.ShiftCompleteAjaxView.as_view(),
        name="shift_complete_ajax"
    ),
    
    # ---------------------------
    # Shift Booking and Unbooking
    # ---------------------------
    
    path(
        "shift/<int:shift_id>/book/",
        views.ShiftBookView.as_view(),
        name="shift_book"
    ),
    path(
        "shift/<int:shift_id>/unbook/",
        views.ShiftUnbookView.as_view(),
        name="shift_unbook"
    ),
    
    # ---------------------------
    # Timesheet Download
    # ---------------------------
    
    path(
        "timesheet/download/",
        views.TimesheetDownloadView.as_view(),
        name="timesheet_download"
    ),
    
    # ---------------------------
    # Report Dashboard
    # ---------------------------
    
    path(
        "report_dashboard/",
        views.ReportDashboardView.as_view(),
        name="report_dashboard"
    ),
    
    # ---------------------------
    # Staffing Forecast
    # ---------------------------
    
    path(
        "staffing_forecast/",
        views.StaffingForecastView.as_view(),
        name="staffing_forecast"
    ),
    
    # ---------------------------
    # Staff Performance
    # ---------------------------
    
    path(
        "staff_performance/",
        views.StaffPerformanceView.as_view(),
        name="staff_performance_list"
    ),
    path(
        "staff_performance/create/",
        views.StaffPerformanceCreateView.as_view(),
        name="staff_performance_create"
    ),
    path(
        "staff_performance/<int:pk>/update/",
        views.StaffPerformanceUpdateView.as_view(),
        name="staff_performance_update"
    ),
    path(
        "staff_performance/<int:pk>/delete/",
        views.StaffPerformanceDeleteView.as_view(),
        name="staff_performance_delete"
    ),
    path(
        "staff_performance/<int:pk>/detail/",
        views.StaffPerformanceDetailView.as_view(),
        name="staff_performance_detail"
    ),
    
    # ---------------------------
    # Shift Details API
    # ---------------------------
    
    path(
        "api/shift/<int:shift_id>/details/",
        views.ShiftDetailsAPIView.as_view(),
        name="shift_details_api"
    ),
    
    # ---------------------------
    # Notifications
    # ---------------------------
    
    path(
        "notifications/",
        views.NotificationListView.as_view(),
        name="notification_list"
    ),
    path(
        "notifications/mark_read/<int:notification_id>/",
        views.MarkNotificationReadView.as_view(),
        name="mark_notification_read"
    ),
]