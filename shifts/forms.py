# /workspace/shiftwise/shifts/forms.py

import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import Agency
from core.forms import AddressFormMixin
from shifts.models import Shift, ShiftAssignment, StaffPerformance
from shifts.validators import validate_image
from shiftwise.utils import geocode_address

User = get_user_model()


class ShiftForm(AddressFormMixin, forms.ModelForm):
    """
    Form for creating and updating Shift instances.
    Integrates Google Places Autocomplete for address fields.
    Includes 'agency' field, required only for superusers.
    """

    class Meta:
        model = Shift
        fields = [
            "name",
            "shift_code",
            "shift_date",
            "start_time",
            "end_time",
            "end_date",
            "is_overnight",
            "capacity",
            "shift_type",
            "shift_role",
            "hourly_rate",
            "notes",
            "agency",
            "is_active",
            # Address fields
            "address_line1",
            "address_line2",
            "city",
            "county",
            "country",
            "postcode",
            "latitude",
            "longitude",
        ]
        widgets = {
            # Shift Name Field widget
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter shift name",
                    "id": "id_name",
                }
            ),
            # Date and Time Fields widgets
            "shift_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "placeholder": "Select shift date",
                    "id": "id_shift_date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "placeholder": "Select end date",
                    "id": "id_end_date",
                }
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "placeholder": "Select start time",
                    "id": "id_start_time",
                }
            ),
            "end_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "placeholder": "Select end time",
                    "id": "id_end_time",
                }
            ),
            "shift_type": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_shift_type",
                }
            ),
            "shift_role": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_shift_role",
                }
            ),
            "agency": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_agency",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "id": "id_is_active",
                }
            ),
            # Address fields
            "address_line1": forms.TextInput(
                attrs={
                    "class": "form-control address-autocomplete",
                    "placeholder": "Enter address line 1",
                    "autocomplete": "address-line1",
                    "id": "id_address_line1",
                }
            ),
            "address_line2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter address line 2",
                    "autocomplete": "address-line2",
                    "id": "id_address_line2",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter city",
                    "autocomplete": "address-level2",
                    "id": "id_city",
                }
            ),
            "county": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter county",
                    "autocomplete": "administrative-area",
                    "id": "id_county",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter country",
                    "readonly": "readonly",
                    "autocomplete": "country-name",
                    "id": "id_country",
                }
            ),
            "postcode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter postcode",
                    "autocomplete": "postal-code",
                    "id": "id_postcode",
                }
            ),
            "latitude": forms.HiddenInput(
                attrs={
                    "id": "id_latitude",
                }
            ),
            "longitude": forms.HiddenInput(
                attrs={
                    "id": "id_longitude",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(ShiftForm, self).__init__(*args, **kwargs)

        # Initialize FormHelper for crispy_forms
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("name", css_class="form-group col-md-6 mb-0"),
                Column("shift_code", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("shift_date", css_class="form-group col-md-6 mb-0"),
                Column("end_date", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("start_time", css_class="form-group col-md-6 mb-0"),
                Column("end_time", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("is_overnight", css_class="form-group col-md-6 mb-0"),
                Column("capacity", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("hourly_rate", css_class="form-group col-md-6 mb-0"),
                Column("shift_type", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("shift_role", css_class="form-group col-md-6 mb-0"),
                Column("agency", css_class="form-group col-md-6 mb-0"),
            ),
            "notes",
            "is_active",
            "address_line1",
            "address_line2",
            Row(
                Column("city", css_class="form-group col-md-4 mb-0"),
                Column("county", css_class="form-group col-md-4 mb-0"),
                Column("postcode", css_class="form-group col-md-4 mb-0"),
            ),
            "country",
            # Hidden fields
            Field("latitude"),
            Field("longitude"),
        )

        # Conditional display and requirement of 'agency' and 'is_active' fields
        if self.user and self.user.is_superuser:
            self.fields["agency"].required = True
            self.fields["is_active"].required = False
        else:
            self.fields["agency"].widget = forms.HiddenInput()
            self.fields["agency"].required = False
            self.fields["is_active"].widget = forms.HiddenInput()
            self.fields["is_active"].required = False

        # 'form-control' class to fields not already specified
        for field_name, field in self.fields.items():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-control"

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

    def clean_postcode(self):
        """
        Validates the postcode based on UK-specific formats.
        """
        postcode = self.cleaned_data.get("postcode")
        if postcode:
            postcode = postcode.strip()
        else:
            postcode = ""

        if not postcode:
            # If no postcode is provided, return it as is
            return postcode

        # UK postcode regex
        uk_postcode_regex = r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$"
        if not re.match(uk_postcode_regex, postcode.upper()):
            raise ValidationError("Enter a valid UK postcode.")
        return postcode.upper()

    def clean_latitude(self):
        """
        Validates the latitude value.
        """
        latitude = self.cleaned_data.get("latitude")
        if latitude is None:
            return latitude
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
            return longitude
        try:
            longitude = float(longitude)
        except ValueError:
            raise ValidationError("Invalid longitude value.")
        if not (-180 <= longitude <= 180):
            raise ValidationError("Longitude must be between -180 and 180.")
        return longitude

    def save(self, commit=True):
        """
        Overrides the save method to correctly handle the shift_code and agency attributes.
        """
        shift = super().save(commit=False)

        # Set agency based on user if not superuser and agency is not set in the form
        if not shift.agency and self.user and not self.user.is_superuser:
            if hasattr(self.user, "profile") and hasattr(self.user.profile, "agency"):
                shift.agency = self.user.profile.agency
            else:
                raise ValidationError("User does not have an associated agency.")

        # Generate shift_code after ensuring agency is set
        if not shift.shift_code:
            shift.shift_code = shift.generate_shift_code()

        # Perform model validations
        shift.clean(skip_date_validation=False)

        if commit:
            shift.save()
            self.save_m2m()
        return shift


class ShiftFilterForm(forms.Form):
    """
    Form for filtering shifts based on date range, status, search queries, shift code, and location/address.
    """

    STATUS_CHOICES = [
        ("all", "All"),
        ("available", "Available"),
        ("booked", "Booked"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control", "id": "id_date_from"}
        ),
        label="Date From",
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control", "id": "id_date_to"}
        ),
        label="Date To",
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_status"}),
        label="Status",
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search by name, agency, or shift type",
                "class": "form-control",
                "id": "id_search",
            }
        ),
        label="Search",
    )
    shift_code = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search by shift code",
                "class": "form-control",
                "id": "id_shift_code",
            }
        ),
        label="Shift Code",
    )
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search by address",
                "class": "form-control address-autocomplete",
                "id": "id_address",
            }
        ),
        label="Address",
    )

    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_latitude"}),
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_longitude"}),
    )

    def __init__(self, *args, **kwargs):
        super(ShiftFilterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"
        self.helper.layout = Layout(
            Row(
                Column("date_from", css_class="form-group col-md-3 mb-0"),
                Column("date_to", css_class="form-group col-md-3 mb-0"),
                Column("status", css_class="form-group col-md-3 mb-0"),
                Column("search", css_class="form-group col-md-3 mb-0"),
            ),
            Row(
                Column("shift_code", css_class="form-group col-md-3 mb-0"),
                Column("address", css_class="form-group col-md-9 mb-0"),
            ),
            # Hidden fields
            Field("latitude"),
            Field("longitude"),
        )


class ShiftCompletionForm(forms.Form):
    """
    Form for completing a shift, capturing digital signature and location data.
    Includes attendance status for supervisors or managers to set.
    """

    signature = forms.CharField(widget=forms.HiddenInput(), required=False)
    latitude = forms.DecimalField(
        widget=forms.HiddenInput(attrs={"id": "id_shift_completion_latitude"}),
        max_digits=9,
        decimal_places=6,
        required=False,
    )
    longitude = forms.DecimalField(
        widget=forms.HiddenInput(attrs={"id": "id_shift_completion_longitude"}),
        max_digits=9,
        decimal_places=6,
        required=False,
    )
    attendance_status = forms.ChoiceField(
        choices=ShiftAssignment.ATTENDANCE_STATUS_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        help_text="Select attendance status after completing the shift.",
    )

    class Meta:
        pass  # No model associated

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize FormHelper for crispy_forms
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "signature",
            "latitude",
            "longitude",
            Row(
                Column("attendance_status", css_class="form-group col-md-12 mb-0"),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        signature = cleaned_data.get("signature")
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        attendance_status = cleaned_data.get("attendance_status")

        # If signature is provided, validate its format
        if signature:
            try:
                format, imgstr = signature.split(";base64,")
                ext = format.split("/")[-1]
            except Exception as e:
                raise ValidationError("Invalid signature data.")

        # If latitude and longitude are provided, validate their ranges
        if (latitude is not None and longitude is None) or (
            latitude is None and longitude is not None
        ):
            raise ValidationError(
                "Both latitude and longitude must be provided together."
            )

        # Validate attendance_status
        if (
            attendance_status
            not in dict(ShiftAssignment.ATTENDANCE_STATUS_CHOICES).keys()
        ):
            raise ValidationError("Invalid attendance status selected.")

        return cleaned_data


class StaffPerformanceForm(forms.ModelForm):
    class Meta:
        model = StaffPerformance
        fields = ["wellness_score", "performance_rating", "status", "comments"]
        widgets = {
            "wellness_score": forms.NumberInput(
                attrs={"class": "form-control", "id": "id_wellness_score"}
            ),
            "performance_rating": forms.NumberInput(
                attrs={"class": "form-control", "id": "id_performance_rating"}
            ),
            "status": forms.Select(attrs={"class": "form-control", "id": "id_status"}),
            "comments": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "id": "id_comments"}
            ),
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
    """
    Form for assigning a worker to a shift.
    Includes a hidden 'worker' field and a 'role' dropdown.
    """

    worker = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.HiddenInput(),
        required=True,
    )
    role = forms.ChoiceField(
        choices=ShiftAssignment.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_role"}),
        label="Role",
    )

    def __init__(self, *args, **kwargs):
        shift = kwargs.pop("shift", None)
        user = kwargs.pop("user", None)
        worker = kwargs.pop("worker", None)
        super().__init__(*args, **kwargs)

        if shift and user:
            if user.is_superuser:
                # Superuser can assign any active Agency Staff not already assigned to the shift
                self.fields["worker"].queryset = User.objects.filter(
                    groups__name="Agency Staff",
                    is_active=True,
                ).exclude(shift_assignments__shift=shift)
            elif user.groups.filter(name="Agency Managers").exists():
                # Agency Managers can assign Agency Staff within their own agency
                self.fields["worker"].queryset = User.objects.filter(
                    profile__agency=shift.agency,
                    groups__name="Agency Staff",
                    is_active=True,
                ).exclude(shift_assignments__shift=shift)
            else:
                # Other users cannot assign workers
                self.fields["worker"].queryset = User.objects.none()

        # Pre-set the worker instance if provided
        if worker:
            self.fields["worker"].initial = worker.id

    def clean_worker(self):
        worker = self.cleaned_data.get("worker")
        if not worker:
            raise forms.ValidationError("Worker is required to assign.")
        return worker

    def clean_role(self):
        role = self.cleaned_data.get("role")
        valid_roles = dict(ShiftAssignment.ROLE_CHOICES).keys()
        if role not in valid_roles:
            raise forms.ValidationError("Invalid role selected.")
        return role


class UnassignWorkerForm(forms.Form):
    """
    Form for unassigning a worker from a shift.
    Includes a hidden 'worker_id' field.
    """

    worker_id = forms.IntegerField(
        widget=forms.HiddenInput(attrs={"id": "id_worker_id"})
    )
