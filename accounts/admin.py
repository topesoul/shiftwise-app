from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency')
    search_fields = ('user__username', 'agency__name')
    list_filter = ('agency',)
