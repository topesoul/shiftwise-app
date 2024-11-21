# /workspace/shiftwise/core/constants.py

# Role Choices
ROLE_CHOICES = (
    ("staff", "Staff"),
    ("agency_manager", "Agency Manager"),
    ("agency_owner", "Agency Owner"),
)

# Agency Type Choices
AGENCY_TYPE_CHOICES = [
    ("staffing", "Staffing"),
    ("healthcare", "Healthcare"),
    ("training", "Training"),
    ("education", "Education"),
    ("other", "Other"),
]

# Shift Type Choices
SHIFT_TYPE_CHOICES = [
    ("regular", "Regular"),
    ("morning_shift", "Morning Shift"),
    ("day_shift", "Day Shift"),
    ("night_shift", "Night Shift"),
    ("bank_holiday", "Bank Holiday"),
    ("emergency_shift", "Emergency Shift"),
    ("overtime", "Overtime"),
]

# Shift Status Choices
STATUS_CHOICES = [
    ('all', 'All'),
    ('available', 'Available'),
    ('booked', 'Booked'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

# Attendance Status Choices
ATTENDANCE_STATUS_CHOICES = (
    ("attended", "Attended"),
    ("late", "Late"),
    ("no_show", "No Show"),
)

# Staff Performance Status Choices
STAFF_PERFORMANCE_STATUS_CHOICES = [
    ("Excellent", "Excellent"),
    ("Good", "Good"),
    ("Average", "Average"),
    ("Poor", "Poor"),
]
