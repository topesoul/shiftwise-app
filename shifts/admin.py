# /workspace/shiftwise/shifts/admin.py

from django.contrib import admin

from .models import Shift, ShiftAssignment


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "shift_date",
        "start_time",
        "end_time",
        "agency",
        "status",
        "get_is_full",
    )
    list_filter = ("shift_type", "status", "agency")
    search_fields = ("name", "agency__name", "postcode", "city", "county", "country")
    ordering = ("shift_date", "start_time")

    def get_is_full(self, obj):
        return obj.is_full

    get_is_full.short_description = "Is Full"
    get_is_full.boolean = True


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "worker",
        "shift",
        "role",
        "status",
        "attendance_status",
        "assigned_at",
    )
    list_filter = ("status", "attendance_status", "role", "shift__agency")
    search_fields = (
        "worker__username",
        "worker__email",
        "shift__name",
        "shift__agency__name",
        "attendance_status",
    )
    ordering = ("-assigned_at",)
    raw_id_fields = ("worker", "shift")  # Improves performance for large datasets

    # Adding filters and actions for better admin management
    actions = ["mark_attended", "mark_late", "mark_no_show"]

    def mark_attended(self, request, queryset):
        updated = queryset.update(attendance_status="attended")
        self.message_user(request, f"{updated} shift assignments marked as Attended.")

    mark_attended.short_description = "Mark selected assignments as Attended"

    def mark_late(self, request, queryset):
        updated = queryset.update(attendance_status="late")
        self.message_user(request, f"{updated} shift assignments marked as Late.")

    mark_late.short_description = "Mark selected assignments as Late"

    def mark_no_show(self, request, queryset):
        updated = queryset.update(attendance_status="no_show")
        self.message_user(request, f"{updated} shift assignments marked as No Show.")

    mark_no_show.short_description = "Mark selected assignments as No Show"
