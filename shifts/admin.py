# /workspace/shiftwise/shifts/admin.py

import logging
from decimal import Decimal
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, F, FloatField, ExpressionWrapper, Count
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

from .models import Shift, ShiftAssignment, StaffPerformance

# Initialize logger
logger = logging.getLogger(__name__)

# ---------------------------
# Custom List Filters
# ---------------------------

class ShiftCapacityFilter(SimpleListFilter):
    title = _('Capacity Status')
    parameter_name = 'capacity_status'

    def lookups(self, request, model_admin):
        return (
            ('full', _('Full')),
            ('available', _('Available')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'full':
            return queryset.annotate(assignments_count=Count('assignments')).filter(assignments_count__gte=F('capacity'))
        elif self.value() == 'available':
            return queryset.annotate(assignments_count=Count('assignments')).filter(assignments_count__lt=F('capacity'))
        return queryset

class AttendanceStatusFilter(SimpleListFilter):
    title = _('Attendance Status')
    parameter_name = 'attendance_status'

    def lookups(self, request, model_admin):
        return (
            ('attended', _('Attended')),
            ('late', _('Late')),
            ('no_show', _('No Show')),
        )

    def queryset(self, request, queryset):
        if self.value() in ['attended', 'late', 'no_show']:
            return queryset.filter(attendance_status=self.value())
        return queryset

# ---------------------------
# Inlines
# ---------------------------

class ShiftAssignmentInline(admin.TabularInline):
    """
    Inline admin interface for ShiftAssignment within ShiftAdmin.
    """
    model = ShiftAssignment
    extra = 0
    readonly_fields = ("assigned_at", "completion_time", "signature", "view_shift_assignment")  # Added 'view_shift_assignment'
    can_delete = True
    show_change_link = True
    fields = (
        "worker",
        "role",
        "status",
        "attendance_status",
        "assigned_at",
        "completion_time",
        "signature",
        "view_shift_assignment",
    )
    ordering = ("-assigned_at",)

    @admin.display(description='View Details')
    def view_shift_assignment(self, obj):
        """
        Provides a direct link to the ShiftAssignment's change page in the admin.
        """
        url = reverse("admin:shifts_shiftassignment_change", args=[obj.id])
        return format_html('<a href="{}">View</a>', url)

# ---------------------------
# Admin Classes
# ---------------------------

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """
    Admin interface for the Shift model.
    """
    list_display = (
        "name",
        "shift_date",
        "start_time",
        "end_time",
        "agency",
        "status",
        "is_full",
        "total_hours",
        "total_pay",
        "view_shift",
    )
    list_filter = ("shift_type", "status", "agency", ShiftCapacityFilter)
    search_fields = (
        "name",
        "agency__name",
        "postcode",
        "city",
        "county",
        "country",
        "assignments__worker__username",
        "assignments__worker__email",
    )
    ordering = ("shift_date", "start_time")
    readonly_fields = ("shift_code", "duration", "is_full", "total_hours", "total_pay")
    fieldsets = (
        (None, {
            'fields': ('name', 'shift_code', 'shift_date', 'end_date')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'is_overnight', 'duration')
        }),
        ('Capacity & Role', {
            'fields': ('capacity', 'shift_type', 'shift_role')
        }),
        ('Agency & Status', {
            'fields': ('agency', 'status', 'is_active', 'is_full')
        }),
        ('Financials', {
            'fields': ('hourly_rate', 'total_pay', 'total_hours')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Location', {
            'fields': (
                'address_line1',
                'address_line2',
                'city',
                'county',
                'country',
                'postcode',
                'latitude',
                'longitude',
            )
        }),
        ('Completion', {
            'fields': ('is_completed', 'completion_time', 'signature')
        }),
    )
    inlines = [ShiftAssignmentInline]

    @admin.display(description='Total Hours')
    def total_hours(self, obj):
        """
        Computes the total hours for the shift by multiplying duration with confirmed assignments count.
        """
        assignment_count = obj.assignments.filter(status=ShiftAssignment.CONFIRMED).count()
        if obj.duration is None:
            return "0"
        total = obj.duration * assignment_count
        return total

    @admin.display(description='Total Pay (£)')
    def total_pay(self, obj):
        """
        Computes the total pay for the shift by multiplying duration, hourly_rate, and confirmed assignments count.
        """
        assignment_count = obj.assignments.filter(status=ShiftAssignment.CONFIRMED).count()

        if obj.duration is None:
            return "£0.00"

        # Convert float to Decimal using string to preserve precision
        duration_decimal = Decimal(str(obj.duration))

        # Perform arithmetic operations using Decimal
        total = duration_decimal * obj.hourly_rate * assignment_count

        # Format the total pay
        return f"£{total:.2f}"

    @admin.display(description='View Details')
    def view_shift(self, obj):
        """
        Provides a direct link to the shift's change page in the admin.
        """
        url = reverse("admin:shifts_shift_change", args=[obj.id])
        return format_html('<a href="{}">View</a>', url)

    def get_queryset(self, request):
        """
        Optimizes queryset performance by selecting related fields.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('agency').prefetch_related('assignments__worker')
        return queryset

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for the ShiftAssignment model.
    """
    list_display = (
        "worker",
        "shift",
        "role",
        "status",
        "attendance_status",
        "assigned_at",
        "completion_time",
        "view_assignment",
    )
    list_filter = ("status", "attendance_status", "role", "shift__agency", AttendanceStatusFilter)
    search_fields = (
        "worker__username",
        "worker__email",
        "shift__name",
        "shift__agency__name",
        "attendance_status",
    )
    ordering = ("-assigned_at",)
    raw_id_fields = ("worker", "shift")
    readonly_fields = ("assigned_at", "completion_time", "signature")
    fieldsets = (
        (None, {
            'fields': ('worker', 'shift', 'role', 'status', 'attendance_status')
        }),
        ('Completion Details', {
            'fields': (
                'completion_time',
                'completion_latitude',
                'completion_longitude',
                'signature',
            )
        }),
    )
    actions = ["mark_attended", "mark_late", "mark_no_show"]

    @admin.display(description='View Details')
    def view_assignment(self, obj):
        """
        Provides a direct link to the ShiftAssignment's change page in the admin.
        """
        url = reverse("admin:shifts_shiftassignment_change", args=[obj.id])
        return format_html('<a href="{}">View</a>', url)

    @admin.action(description='Mark selected assignments as Attended')
    def mark_attended(self, request, queryset):
        updated = queryset.update(attendance_status="attended")
        self.message_user(request, f"{updated} shift assignments marked as Attended.")
        logger.info(f"{updated} shift assignments marked as Attended by {request.user.username}.")

    @admin.action(description='Mark selected assignments as Late')
    def mark_late(self, request, queryset):
        updated = queryset.update(attendance_status="late")
        self.message_user(request, f"{updated} shift assignments marked as Late.")
        logger.info(f"{updated} shift assignments marked as Late by {request.user.username}.")

    @admin.action(description='Mark selected assignments as No Show')
    def mark_no_show(self, request, queryset):
        updated = queryset.update(attendance_status="no_show")
        self.message_user(request, f"{updated} shift assignments marked as No Show.")
        logger.info(f"{updated} shift assignments marked as No Show by {request.user.username}.")

    def get_queryset(self, request):
        """
        Optimizes queryset performance by selecting related fields.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('worker', 'shift__agency')
        return queryset

@admin.register(StaffPerformance)
class StaffPerformanceAdmin(admin.ModelAdmin):
    """
    Admin interface for the StaffPerformance model.
    """
    list_display = (
        "worker",
        "shift",
        "wellness_score",
        "performance_rating",
        "status",
        "created_at",
        "view_performance",
    )
    list_filter = ("status", "worker__profile__agency")
    search_fields = (
        "worker__username",
        "worker__email",
        "shift__name",
        "shift__agency__name",
        "comments",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("worker", "shift")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {
            'fields': ('worker', 'shift')
        }),
        ('Performance Metrics', {
            'fields': ('wellness_score', 'performance_rating', 'status', 'comments')
        }),
        ('Audit', {
            'fields': ('created_at',)
        }),
    )
    actions = ["mark_excellent", "mark_good", "mark_average", "mark_poor"]

    @admin.display(description='View Details')
    def view_performance(self, obj):
        """
        Provides a direct link to the StaffPerformance's change page in the admin.
        """
        url = reverse("admin:shifts_staffperformance_change", args=[obj.id])
        return format_html('<a href="{}">View</a>', url)

    @admin.action(description='Mark selected performances as Excellent')
    def mark_excellent(self, request, queryset):
        updated = queryset.update(status="Excellent")
        self.message_user(request, f"{updated} staff performances marked as Excellent.")
        logger.info(f"{updated} staff performances marked as Excellent by {request.user.username}.")

    @admin.action(description='Mark selected performances as Good')
    def mark_good(self, request, queryset):
        updated = queryset.update(status="Good")
        self.message_user(request, f"{updated} staff performances marked as Good.")
        logger.info(f"{updated} staff performances marked as Good by {request.user.username}.")

    @admin.action(description='Mark selected performances as Average')
    def mark_average(self, request, queryset):
        updated = queryset.update(status="Average")
        self.message_user(request, f"{updated} staff performances marked as Average.")
        logger.info(f"{updated} staff performances marked as Average by {request.user.username}.")

    @admin.action(description='Mark selected performances as Poor')
    def mark_poor(self, request, queryset):
        updated = queryset.update(status="Poor")
        self.message_user(request, f"{updated} staff performances marked as Poor.")
        logger.info(f"{updated} staff performances marked as Poor by {request.user.username}.")

    def get_queryset(self, request):
        """
        Optimizes queryset performance by selecting related fields.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('worker', 'shift__agency')
        return queryset
