from django.contrib import admin
from .models import Shift
from .forms import ShiftForm

# Register your models here.
@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    form = ShiftForm
    list_display = ('name', 'shift_date', 'start_time', 'end_time', 'city')
    search_fields = ('name', 'city', 'postcode')
    list_filter = ('shift_date', 'city', 'country')