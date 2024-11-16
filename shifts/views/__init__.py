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
    StaffPerformanceView,
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
)

# Dashboard Views
from .dashboard_views import (
    DashboardView,
)


# Custom Views
from shifts.views.custom_views import (
    custom_permission_denied_view,
    custom_page_not_found_view,
    custom_server_error_view,
)
