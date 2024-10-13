# shifts/admin.py

from django.contrib import admin
from .models import Agency, Shift, ShiftAssignment


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    """
    Admin interface for the Agency model.
    """
    list_display = ('name', 'address_display', 'agency_code', 'email', 'phone_number', 'created_at')
    search_fields = ('name', 'agency_code', 'email')
    ordering = ('name',)

    def address_display(self, obj):
        """
        Combines address_line1, address_line2, city, state, and country for display.
        """
        address_parts = [
            obj.address_line1,
            obj.address_line2 or '',
            obj.city,
            obj.state or '',
            obj.country or ''
        ]
        return ', '.join(filter(None, address_parts))
    address_display.short_description = 'Address'


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """
    Admin interface for the Shift model.
    """
    list_display = ('name', 'shift_date', 'start_time', 'end_time', 'city', 'agency', 'status')
    search_fields = ('name', 'city', 'postcode')
    list_filter = ('shift_date', 'city', 'agency', 'status', 'shift_type')
    ordering = ('shift_date', 'start_time')

    def get_queryset(self, request):
        """
        Restricts agency admins to see only their own agency's shifts.
        Superusers see all shifts.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers see all shifts
        if hasattr(request.user, 'profile') and request.user.profile.agency:
            return qs.filter(agency=request.user.profile.agency)
        else:
            return qs.none()  # If the user has no agency, return empty queryset

    def get_search_results(self, request, queryset, search_term):
        """
        Limits search results to shifts within the current user's agency.
        Superusers search across all shifts.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if not request.user.is_superuser and hasattr(request.user, 'profile') and request.user.profile.agency:
            queryset = queryset.filter(agency=request.user.profile.agency)
        return queryset, use_distinct


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for the ShiftAssignment model.
    """
    list_display = ('worker', 'shift', 'assigned_at', 'role', 'status')
    list_filter = ('shift__agency', 'shift__shift_date', 'status', 'role')
    search_fields = ('worker__username', 'shift__name', 'shift__agency__name')
    ordering = ('-assigned_at',)

    def get_queryset(self, request):
        """
        Restricts agency admins to see only their own agency's shift assignments.
        Superusers see all assignments.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers see all shift assignments
        if hasattr(request.user, 'profile') and request.user.profile.agency:
            return qs.filter(shift__agency=request.user.profile.agency)
        else:
            return qs.none()  # If the user has no agency, return empty queryset

    def get_search_results(self, request, queryset, search_term):
        """
        Limits search results to shift assignments within the current user's agency.
        Superusers search across all assignments.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if not request.user.is_superuser and hasattr(request.user, 'profile') and request.user.profile.agency:
            queryset = queryset.filter(shift__agency=request.user.profile.agency)
        return queryset, use_distinct