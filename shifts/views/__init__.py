# /workspace/shiftwise/shifts/views/__init__.py

__all__ = [
    # Staff Management Views
    "StaffListView",
    "StaffCreateView",
    "StaffUpdateView",
    "StaffDeleteView",
    # Shift Management Views
    "ShiftListView",
    "ShiftCreateView",
    "ShiftUpdateView",
    "ShiftDeleteView",
    "ShiftDetailView",
    # Shift Completion Views
    "ShiftCompleteView",
    "ShiftCompleteForUserView",
    "ShiftCompleteAjaxView",
    # Shift Booking Views
    "ShiftBookView",
    "ShiftUnbookView",
    # Staff Performance Views
    "StaffPerformanceListView",
    "StaffPerformanceDetailView",
    "StaffPerformanceCreateView",
    "StaffPerformanceUpdateView",
    "StaffPerformanceDeleteView",
    # Reporting Views
    "TimesheetDownloadView",
    "ReportDashboardView",
    # Assignment Views
    "AssignWorkerView",
    "UnassignWorkerView",
    # API Views
    "ShiftDetailsAPIView",
    "APIAccessView",
    # Dashboard Views
    "DashboardView",
    # Custom Views
    "custom_permission_denied_view",
    "custom_page_not_found_view",
    "custom_server_error_view",
]

# Custom Views
from shifts.views.custom_views import (custom_page_not_found_view,
                                       custom_permission_denied_view,
                                       custom_server_error_view)

# API Views
from .api_views import APIAccessView, ShiftDetailsAPIView
# Assignment Views
from .assignment_views import AssignWorkerView, UnassignWorkerView
# Shift Booking Views
from .booking_views import ShiftBookView, ShiftUnbookView
# Shift Completion Views
from .completion_views import (ShiftCompleteAjaxView, ShiftCompleteForUserView,
                               ShiftCompleteView)
# Staff Performance Views
from .performance_views import (StaffPerformanceCreateView,
                                StaffPerformanceDeleteView,
                                StaffPerformanceDetailView,
                                StaffPerformanceListView,
                                StaffPerformanceUpdateView)
# Reporting Views
from .report_views import ReportDashboardView, TimesheetDownloadView
# Shift Management Views
from .shift_views import (ShiftCreateView, ShiftDeleteView, ShiftDetailView,
                          ShiftListView, ShiftUpdateView)
# Staff Management Views
from .staff_views import (StaffCreateView, StaffDeleteView, StaffListView,
                          StaffUpdateView)
