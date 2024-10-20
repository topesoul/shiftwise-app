# shifts/forms.py

from django import forms
from .models import Shift
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import Profile
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


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
                'id': 'id_name'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'step': '60',
                'class': 'form-control',
                'id': 'id_start_time'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'step': '60',
                'class': 'form-control',
                'id': 'id_end_time'
            }),
            'shift_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_shift_date'
            }),
            'capacity': forms.NumberInput(attrs={
                'min': '1',
                'class': 'form-control',
                'placeholder': 'Enter capacity',
                'id': 'id_capacity'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'class': 'form-control',
                'placeholder': 'Enter hourly rate',
                'id': 'id_hourly_rate'
            }),
            'postcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter postcode',
                'id': 'id_postcode'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address line 1',
                'id': 'id_address_line1'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city',
                'id': 'id_city'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state',
                'id': 'id_state'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter country',
                'id': 'id_country'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'id': 'id_latitude'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'id': 'id_longitude'
            }),
            'shift_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_shift_type'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Enter any additional notes (optional)',
                'id': 'id_notes'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        shift_date = cleaned_data.get("shift_date")
        capacity = cleaned_data.get("capacity")
        hourly_rate = cleaned_data.get("hourly_rate")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        # Ensure that shifts cannot be created in the past
        if shift_date and shift_date < timezone.now().date():
            self.add_error('shift_date', "Shift date cannot be in the past.")

        # Validate capacity
        if capacity and capacity < 1:
            self.add_error('capacity', "Capacity must be at least 1.")

        # Validate hourly rate
        if hourly_rate and hourly_rate <= 0:
            self.add_error('hourly_rate', "Hourly rate must be positive.")

        # Validate start and end times
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "End time must be after start time.")

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not all(part.isalnum() or part.isspace() for part in name):
            raise ValidationError("Shift name should only contain alphanumeric characters and spaces.")
        return name


class StaffCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        if commit:
            user.save()
            # Create Profile
            Profile.objects.create(user=user)
        return user


class StaffUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    is_active = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'is_active')