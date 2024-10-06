from django.contrib import admin
from .models import Shift, ShiftAssignment, Agency

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'shift_date', 'start_time', 'end_time', 'city', 'agency')
    search_fields = ('name', 'city', 'postcode')
    list_filter = ('shift_date', 'city')

    def get_queryset(self, request):
        """
        Override the queryset to restrict agency admins to only see their own agency's shifts.
        Superusers will see all shifts.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers see all shifts
        return qs.filter(agency=request.user.profile.agency)

    def get_search_results(self, request, queryset, search_term):
        """
        Override search to limit results to shifts within the current user's agency (for agency admins).
        Superusers will still search across all shifts.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if not request.user.is_superuser:
            queryset = queryset.filter(agency=request.user.profile.agency)
        return queryset, use_distinct


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('worker', 'shift', 'assigned_at')
    list_filter = ('shift__agency', 'shift__shift_date')
    search_fields = ('worker__username', 'shift__name')
