# /workspace/shiftwise/accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'agency')
    list_select_related = ('profile', )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def agency(self, instance):
        return instance.profile.agency
    agency.short_description = 'Agency'

# Register the custom UserAdmin
admin.site.register(User, UserAdmin)
