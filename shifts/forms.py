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
            'state',
            'country',
            'latitude',
            'longitude',
            'shift_type',
            'hourly_rate',
            'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter shift name',
                'id': 'name'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'step': '60',  # To allow selection in 1-minute increments
                'class': 'form-control',
                'id': 'start_time'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'step': '60',
                'class': 'form-control',
                'id': 'end_time'
            }),
            'shift_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'shift_date'
            }),
            'capacity': forms.NumberInput(attrs={
                'min': '1',
                'class': 'form-control',
                'placeholder': 'Enter capacity',
                'id': 'capacity'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'class': 'form-control',
                'placeholder': 'Enter hourly rate',
                'id': 'hourly_rate'
            }),
            'postcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter postcode',
                'id': 'postcode'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address line 1',
                'id': 'address_line1'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city',
                'id': 'city'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state',
                'id': 'state'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter country',
                'id': 'country'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'id': 'latitude'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'id': 'longitude'
            }),
            'shift_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'shift_type'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Enter any additional notes (optional)',
                'id': 'notes'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        shift_date = cleaned_data.get("shift_date")
        capacity = cleaned_data.get("capacity")
        hourly_rate = cleaned_data.get("hourly_rate")


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
        if not all(part.isalpha() for part in name.split()):
            raise ValidationError("Shift name should only contain alphabetic characters and spaces.")
        return name
