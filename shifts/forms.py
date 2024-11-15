# /workspace/shiftwise/shifts/forms.py

import re
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Shift, ShiftAssignment, StaffPerformance
from accounts.models import Agency
from django.contrib.auth import get_user_model

User = get_user_model()

class ShiftForm(forms.ModelForm):
    """
    Form for creating and updating Shift instances.
    Integrates Google Places Autocomplete for address fields.
    Includes 'agency' field, required only for superusers.
    """

    class Meta:
        model = Shift
        fields = [
            "name",
            "shift_date",
            "start_time",
            "end_time",
            "end_date",
            "is_overnight",
            "capacity",
            "address_line1",
            "address_line2",
            "city",
            "county",
            "postcode",
            "country",
            "latitude",
            "longitude",
            "shift_type",
            "hourly_rate",
            "notes",
            "agency",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter shift name",
                    "id": "id_name",
                }
            ),
            "shift_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control", "id": "id_shift_date"}
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "step": "60",
                    "class": "form-control",
                    "id": "id_start_time",
                }
            ),
            "end_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "step": "60",
                    "class": "form-control",
                    "id": "id_end_time",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control datepicker",
                    "id": "id_end_date",
                }
            ),
            "capacity": forms.NumberInput(
                attrs={
                    "min": "1",
                    "class": "form-control",
                    "placeholder": "Enter capacity",
                    "id": "id_capacity",
                }
            ),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0.01",
                    "class": "form-control",
                    "placeholder": "Enter hourly rate",
                    "id": "id_hourly_rate",
                }
            ),
            # Address Fields
            "address_line1": forms.TextInput(
                attrs={
                    "class": "form-control address-autocomplete",
                    "placeholder": "Enter address line 1",
                    "id": "id_address_line1",
                }
            ),
            "address_line2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter address line 2",
                    "id": "id_address_line2",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter city",
                    "id": "id_city",
                }
            ),
            "county": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter county",
                    "id": "id_county",
                }
            ),
            "postcode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter postcode",
                    "id": "id_postcode",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter country",
                    "id": "id_country",
                }
            ),
            "latitude": forms.HiddenInput(attrs={"id": "id_latitude"}),
            "longitude": forms.HiddenInput(attrs={"id": "id_longitude"}),
            "shift_type": forms.Select(
                attrs={"class": "form-control", "id": "id_shift_type"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Enter any additional notes (optional)",
                    "id": "id_notes",
                }
            ),
            "agency": forms.Select(attrs={"class": "form-control", "id": "id_agency"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(ShiftForm, self).__init__(*args, **kwargs)
        if user and user.is_superuser:
            self.fields["agency"].required = True
        else:
            self.fields["agency"].widget = forms.HiddenInput()
            self.fields["agency"].required = False

    def clean(self):
        cleaned_data = super().clean()
        shift_date = cleaned_data.get("shift_date")
        end_date = cleaned_data.get("end_date")
        capacity = cleaned_data.get("capacity")
        hourly_rate = cleaned_data.get("hourly_rate")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        is_overnight = cleaned_data.get("is_overnight")

        # Ensure that shifts cannot be created in the past
        if shift_date and shift_date < timezone.now().date():
            self.add_error("shift_date", "Shift date cannot be in the past.")

        # Ensure end_date is after or equal to shift_date
        if end_date and shift_date and end_date < shift_date:
            self.add_error("end_date", "End date cannot be before shift date.")

        # Validate capacity
        if capacity and capacity < 1:
            self.add_error("capacity", "Capacity must be at least 1.")

        # Validate hourly rate
        if hourly_rate and hourly_rate <= 0:
            self.add_error("hourly_rate", "Hourly rate must be positive.")

        # Validate start and end times, accounting for overnight shifts
        if start_time and end_time:
            if not is_overnight and start_time >= end_time:
                self.add_error(
                    "end_time",
                    "End time must be after start time if the shift is not overnight.",
                )
            elif is_overnight and start_time == end_time:
                self.add_error(
                    "end_time",
                    "End time cannot be the same as start time for an overnight shift.",
                )

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name and not all(part.isalnum() or part.isspace() for part in name):
            raise ValidationError(
                "Shift name should only contain alphanumeric characters and spaces."
            )
        return name

    def clean_postcode(self):
        """
        Validates the postcode based on UK-specific formats.
        """
        postcode = self.cleaned_data.get("postcode", "").strip()
        if not postcode:
            raise ValidationError("Postcode is required.")
        # UK postcode regex
        uk_postcode_regex = r"^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$"
        if not re.match(uk_postcode_regex, postcode.upper()):
            raise ValidationError("Enter a valid UK postcode.")
        return postcode.upper()

    def clean_latitude(self):
        """
        Validates the latitude value.
        """
        latitude = self.cleaned_data.get("latitude")
        if latitude is None:
            raise ValidationError("Latitude is required.")
        try:
            latitude = float(latitude)
        except ValueError:
            raise ValidationError("Invalid latitude value.")
        if not (-90 <= latitude <= 90):
            raise ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        """
        Validates the longitude value.
        """
        longitude = self.cleaned_data.get("longitude")
        if longitude is None:
            raise ValidationError("Longitude is required.")
        try:
            longitude = float(longitude)
        except ValueError:
            raise ValidationError("Invalid longitude value.")
        if not (-180 <= longitude <= 180):
            raise ValidationError("Longitude must be between -180 and 180.")
        return longitude

    def save(self, commit=True):
        """
        Overrides the save method to rely solely on client-side address and coordinate data.
        """
        shift = super().save(commit=False)
        if commit:
            shift.save()
            self.save_m2m()
        return shift


class ShiftCompletionForm(forms.Form):
    """
    Form for completing a shift, capturing digital signature and location data.
    Includes attendance status for supervisors or managers to set.
    """

    signature = forms.CharField(widget=forms.HiddenInput())
    latitude = forms.DecimalField(widget=forms.HiddenInput())
    longitude = forms.DecimalField(widget=forms.HiddenInput())
    attendance_status = forms.ChoiceField(
        choices=ShiftAssignment.ATTENDANCE_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Select attendance status after completing the shift.",
    )

    def clean(self):
        cleaned_data = super().clean()
        signature = cleaned_data.get("signature")
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        attendance_status = cleaned_data.get("attendance_status")

        if not signature:
            raise forms.ValidationError("Signature is required.")
        if latitude is None or longitude is None:
            raise forms.ValidationError("Location data is required.")
        if (
            attendance_status
            and attendance_status
            not in dict(ShiftAssignment.ATTENDANCE_STATUS_CHOICES).keys()
        ):
            raise forms.ValidationError("Invalid attendance status selected.")

        return cleaned_data


class StaffPerformanceForm(forms.ModelForm):
    class Meta:
        model = StaffPerformance
        fields = ["wellness_score", "performance_rating", "status", "comments"]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_wellness_score(self):
        score = self.cleaned_data.get("wellness_score")
        if score < 0 or score > 100:
            raise ValidationError("Wellness score must be between 0 and 100.")
        return score

    def clean_performance_rating(self):
        rating = self.cleaned_data.get("performance_rating")
        if rating < 0 or rating > 5:
            raise ValidationError("Performance rating must be between 0 and 5.")
        return rating

class AssignWorkerForm(forms.Form):
    worker = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Select Worker",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        shift = kwargs.pop('shift', None)
        super().__init__(*args, **kwargs)
        if shift:
            # Filter workers to only those in the same agency and active
            self.fields['worker'].queryset = User.objects.filter(
                groups__name="Agency Staff",
                is_active=True,
                profile__agency=shift.agency
            )
        else:
            # Fallback: list all active agency staff
            self.fields['worker'].queryset = User.objects.filter(
                groups__name="Agency Staff",
                is_active=True
            )

class UnassignWorkerForm(forms.Form):
    worker_id = forms.IntegerField(widget=forms.HiddenInput())