# /workspace/shiftwise/shifts/views/__init__.py

__all__ = [
    # Staff Management Views
    'StaffListView',
    'StaffCreateView',
    'StaffUpdateView',
    'StaffDeleteView',

    # Shift Management Views
    'ShiftListView',
    'ShiftCreateView',
    'ShiftUpdateView',
    'ShiftDeleteView',
    'ShiftDetailView',

    # Shift Completion Views
    'ShiftCompleteView',
    'ShiftCompleteForUserView',
    'ShiftCompleteAjaxView',

    # Shift Booking Views
    'ShiftBookView',
    'ShiftUnbookView',

    # Staff Performance Views
    'StaffPerformanceListView',
    'StaffPerformanceDetailView',
    'StaffPerformanceCreateView',
    'StaffPerformanceUpdateView',
    'StaffPerformanceDeleteView',

    # Reporting Views
    'TimesheetDownloadView',
    'ReportDashboardView',

    # Assignment Views
    'AssignWorkerView',
    'UnassignWorkerView',

    # API Views
    'ShiftDetailsAPIView',
    'APIAccessView',

    # Dashboard Views
    'DashboardView',

    # Custom Views
    'custom_permission_denied_view',
    'custom_page_not_found_view',
    'custom_server_error_view',
]

# Staff Management Views
from .staff_views import (
    StaffListView,
    StaffCreateView,
    StaffUpdateView,
    StaffDeleteView,
)

# Shift Management Views
from .shift_views import (
    ShiftListView,
    ShiftCreateView,
    ShiftUpdateView,
    ShiftDeleteView,
    ShiftDetailView,
)

# Shift Completion Views
from .completion_views import (
    ShiftCompleteView,
    ShiftCompleteForUserView,
    ShiftCompleteAjaxView,
)

# Shift Booking Views
from .booking_views import (
    ShiftBookView,
    ShiftUnbookView,
)

# Staff Performance Views
from .performance_views import (
    StaffPerformanceListView,
    StaffPerformanceDetailView,
    StaffPerformanceCreateView,
    StaffPerformanceUpdateView,
    StaffPerformanceDeleteView,
)

# Reporting Views
from .report_views import (
    TimesheetDownloadView,
    ReportDashboardView,
)

# Assignment Views
from .assignment_views import (
    AssignWorkerView,
    UnassignWorkerView,
)

# API Views
from .api_views import (
    ShiftDetailsAPIView,
    APIAccessView,
)

# Custom Views
from shifts.views.custom_views import (
    custom_permission_denied_view,
    custom_page_not_found_view,
    custom_server_error_view,
)