from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    """
    Defines an inline admin descriptor for Profile model
    which acts a bit like a singleton
    """
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """
    Define a new User admin which includes Profile inline
    """
    inlines = (ProfileInline, )

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'agency')
    list_select_related = ('profile', )

    def agency(self, instance):
        return instance.profile.agency
    agency.short_description = 'Agency'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency')
    search_fields = ('user__username', 'agency__name')
    list_filter = ('agency',)