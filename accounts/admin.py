# /workspace/shiftwise/accounts/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import Profile, Agency, Invitation

User = get_user_model()

# Unregister the default User admin to register a customized one
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ["username", "email", "first_name", "last_name", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_superuser", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["username"]

    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("role",)}),)

    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("role",)}),)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "agency",
        "monthly_view_count",
        "view_count_reset_date",
        "city",
        "county",
        "postcode",
    ]
    search_fields = ["user__username", "agency__name", "city", "county", "postcode"]
    list_filter = ["agency", "country", "county"]

    fieldsets = (
        (None, {"fields": ("user", "agency")}),
        (
            "Address Information",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "county",
                    "state",
                    "country",
                    "postcode",
                )
            },
        ),
        (
            "Additional Information",
            {"fields": ("travel_radius", "latitude", "longitude", "profile_picture")},
        ),
        (
            "Subscription Info",
            {
                "fields": ("monthly_view_count", "view_count_reset_date"),
            },
        ),
    )


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "agency_code",
        "postcode",
        "city",
        "county",
        "state",
        "country",
    ]
    search_fields = [
        "name",
        "agency_code",
        "postcode",
        "city",
        "county",
        "state",
        "country",
    ]
    list_filter = ["agency_type", "is_active", "country", "county"]

    fieldsets = (
        (None, {"fields": ("name", "agency_code", "agency_type", "is_active")}),
        ("Contact Information", {"fields": ("email", "phone_number", "website")}),
        (
            "Address Information",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "county",
                    "state",
                    "country",
                    "postcode",
                )
            },
        ),
        ("Location Coordinates", {"fields": ("latitude", "longitude")}),
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "invited_by",
        "agency",
        "created_at",
        "is_active",
        "accepted_at",
        "is_expired",
    ]
    search_fields = ["email", "invited_by__username", "agency__name"]
    list_filter = ["is_active", "created_at", "accepted_at"]
    ordering = ["-created_at"]
    exclude = ("token",)
    readonly_fields = ("invited_at", "invited_by", "agency", "is_active", "accepted_at")

    fieldsets = (
        (None, {"fields": ("email", "invited_by", "agency")}),
        ("Invitation Status", {"fields": ("is_active", "invited_at", "accepted_at")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    def is_expired(self, obj):
        return obj.is_expired()

    is_expired.boolean = True
    is_expired.short_description = "Expired?"
