from django import forms
from .models import Shift
from django.core.exceptions import ValidationError
from datetime import time

class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'shift_date', 'postcode', 'address_line1', 'city']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        shift_date = cleaned_data.get("shift_date")

        # Validate that end time is after start time
        if start_time and end_time and end_time <= start_time:
            raise ValidationError("End time must be after start time.")
        
        # Ensure that shifts cannot be created in the past
        if shift_date and shift_date < timezone.now().date():
            raise ValidationError("Shift date cannot be in the past.")

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name.isalpha():
            raise ValidationError("Shift name should only contain alphabetic characters.")
        return name
