# /workspace/shiftwise/core/forms.py

import re

from django import forms
from django.core.exceptions import ValidationError


class AddressFormMixin:
    """
    Mixin to include common address validation methods.
    """

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
