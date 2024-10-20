# /workspace/shiftwise/shifts/admin.py

from django.contrib import admin
from .models import Shift, ShiftAssignment, Agency
from accounts.models import Profile  # Importing Profile

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('agency_code', 'name', 'agency_type', 'is_active', 'created_at', 'updated_at', 'manager')
    search_fields = ('agency_code', 'name')
    list_filter = ('agency_type', 'is_active', 'created_at', 'updated_at')

    def manager(self, obj):
        try:
            # Assuming one manager per agency
            manager_profile = obj.users.get(user__role='agency_manager')
            return manager_profile.user.username
        except Profile.DoesNotExist:
            return "No Manager Assigned"
        except Profile.MultipleObjectsReturned:
            return "Multiple Managers Assigned"

    manager.short_description = 'Manager'

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'shift_date', 'start_time', 'end_time', 'agency', 'status')
    list_filter = ('agency', 'status', 'shift_type')
    search_fields = ('name', 'agency__name')

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('shift', 'worker', 'assigned_at', 'role', 'status')
    list_filter = ('status', 'role', 'assigned_at')
    search_fields = ('shift__name', 'worker__username')
