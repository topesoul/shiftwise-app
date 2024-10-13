from django import forms
from .models import Shift
from django.core.exceptions import ValidationError
from django.utils import timezone


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = [
            'name',
            'start_time',
            'end_time',
            'shift_date',
            'capacity',
            'postcode',
            'address_line1',
            'city',
            'shift_type',
            'hourly_rate',
            'notes'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'step': '60',  # Allows selection in 1-minute increments
                'class': 'form-control'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'step': '60',  # Allows selection in 1-minute increments
                'class': 'form-control'
            }),
            'shift_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'capacity': forms.NumberInput(attrs={
                'min': '1',
                'class': 'form-control'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'class': 'form-control'
            }),
            'postcode': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'shift_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        shift_date = cleaned_data.get("shift_date")
        capacity = cleaned_data.get("capacity")
        hourly_rate = cleaned_data.get("hourly_rate")

        # Validate that end time is after start time or spans into the next day
        if start_time and end_time and end_time <= start_time:
            raise ValidationError("End time must be after start time unless it spans into the next day.")

        # Ensure that shifts cannot be created in the past
        if shift_date and shift_date < timezone.now().date():
            raise ValidationError("Shift date cannot be in the past.")

        # Validate capacity
        if capacity and capacity < 1:
            raise ValidationError("Capacity must be at least 1.")

        # Validate hourly rate
        if hourly_rate and hourly_rate <= 0:
            raise ValidationError("Hourly rate must be positive.")

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name.replace(" ", "").isalpha():  # Allow spaces in shift names
            raise ValidationError("Shift name should only contain alphabetic characters and spaces.")
        return name
