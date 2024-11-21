# /workspace/shiftwise/accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Agency, Profile, Invitation, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ["username", "email", "first_name", "last_name", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_superuser", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["username"]

    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("role",)}),
    )

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('agency_code', 'name', 'owner', 'is_active', 'agency_type')
    search_fields = ('name', 'agency_code', 'owner__username', 'email')
    list_filter = ('is_active', 'agency_type')
    raw_id_fields = ('owner',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency', 'travel_radius')
    search_fields = ('user__username', 'agency__name')
    list_filter = ('agency',)

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'invited_by', 'agency', 'is_active', 'invited_at', 'accepted_at')
    search_fields = ('email', 'invited_by__username', 'agency__name')
    list_filter = ('is_active', 'agency')
