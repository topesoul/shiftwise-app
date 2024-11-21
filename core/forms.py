# /workspace/shiftwise/core/forms.py

import re
from django import forms
from django.core.exceptions import ValidationError

class AddressFormMixin:
    """
    Mixin to include common address fields and validation.
    """

    address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control address-autocomplete",
                "placeholder": "Enter address line 1",
                "autocomplete": "address-line1",
            }
        ),
    )
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter address line 2",
                "autocomplete": "address-line2",
            }
        ),
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter city",
                "autocomplete": "address-level2",
            }
        ),
    )
    county = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter county",
                "autocomplete": "administrative-area",
            }
        ),
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter state",
                "autocomplete": "address-level1",
            }
        ),
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter country",
                "readonly": "readonly",
                "autocomplete": "country-name",
            }
        ),
    )
    postcode = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter postcode",
                "autocomplete": "postal-code",
            }
        ),
    )
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(),
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean_postcode(self):
        """Common postcode validation."""
        postcode = self.cleaned_data.get("postcode", "").strip()
        if not postcode:
            return postcode
        # UK postcode regex
        uk_postcode_regex = r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$"
        if not re.match(uk_postcode_regex, postcode.upper()):
            raise ValidationError("Enter a valid UK postcode.")
        return postcode.upper()

    def clean_latitude(self):
        """Common latitude validation."""
        latitude = self.cleaned_data.get("latitude")
        if latitude is None:
            return latitude
        try:
            latitude = float(latitude)
        except (ValueError, TypeError):
            raise ValidationError("Invalid latitude value.")
        if not (-90 <= latitude <= 90):
            raise ValidationError("Latitude must be between -90 and 90.")
        return latitude

    def clean_longitude(self):
        """Common longitude validation."""
        longitude = self.cleaned_data.get("longitude")
        if longitude is None:
            return longitude
        try:
            longitude = float(longitude)
        except (ValueError, TypeError):
            raise ValidationError("Invalid longitude value.")
        if not (-180 <= longitude <= 180):
            raise ValidationError("Longitude must be between -180 and 180.")
        return longitude