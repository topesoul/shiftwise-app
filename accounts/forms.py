# /workspace/shiftwise/accounts/forms.py

import logging
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row
from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps

from core.constants import AGENCY_TYPE_CHOICES, ROLE_CHOICES
from core.forms import AddressFormMixin
from core.utils import assign_user_to_group, generate_unique_code
from shiftwise.utils import geocode_address

from .models import Agency, Invitation, Profile

User = get_user_model()

# Initialize the logger
logger = logging.getLogger(__name__)


class AgencyForm(AddressFormMixin, forms.ModelForm):
    """
    Form for creating and updating Agency instances.
    Integrates Google Places Autocomplete for address fields.
    """

    class Meta:
        model = Agency
        fields = [
            "name",
            "agency_type",
            "email",
            "phone_number",
            "website",
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
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter agency name",
                    "id": "id_name",
                }
            ),
            "agency_type": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_agency_type",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Agency email",
                    "id": "id_email",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone Number",
                    "id": "id_phone_number",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Website URL",
                    "id": "id_website",
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
        super(AgencyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "name",
            "agency_type",
            "address_line1",
            "address_line2",
            Row(
                Column("city", css_class="form-group col-md-4 mb-0"),
                Column("county", css_class="form-group col-md-4 mb-0"),
                Column("postcode", css_class="form-group col-md-4 mb-0"),
            ),
            "country",
            "email",
            "phone_number",
            "website",
            # Hidden fields
            Field("latitude"),
            Field("longitude"),
        )

    def clean_email(self):
        """Ensures the email is valid and not already in use."""
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        # Validate email format
        try:
            forms.EmailField().clean(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        # Check if email already exists
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        """
        Clean method to perform geocoding of the address.
        """
        cleaned_data = super().clean()
        address_line1 = cleaned_data.get("address_line1")
        address_line2 = cleaned_data.get("address_line2")
        city = cleaned_data.get("city")
        county = cleaned_data.get("county")
        postcode = cleaned_data.get("postcode")
        country = cleaned_data.get("country")

        # Construct the full address
        address_components = [
            address_line1,
            address_line2,
            city,
            county,
            postcode,
            country,
        ]
        full_address = ", ".join(filter(None, address_components))

        if full_address.strip():
            try:
                geocode_result = geocode_address(full_address)
                cleaned_data["latitude"] = geocode_result["latitude"]
                cleaned_data["longitude"] = geocode_result["longitude"]
                logger.info(f"Geocoded address for agency: {full_address}")
            except Exception as e:
                logger.error(f"Failed to geocode address for agency: {e}")
                self.add_error(None, "Invalid address. Please enter a valid address.")
        else:
            self.add_error("address_line1", "Address fields cannot be empty.")
        return cleaned_data


    def clean_postcode(self):
        """
        Validates the postcode based on UK-specific formats.
        """
        postcode = self.cleaned_data.get("postcode", "")
        if postcode:
            postcode = postcode.strip()

        # Handle empty postcode case
        if not postcode:
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
        Overrides the save method to correctly handle the agency attributes.
        """
        agency = super().save(commit=False)

        # Generate unique agency code if necessary
        if not agency.agency_code:
            agency.agency_code = generate_unique_code()

        # Perform model validations
        agency.clean()

        if commit:
            agency.save()
            self.save_m2m()
        return agency


class AgencySignUpForm(AddressFormMixin, UserCreationForm):
    """
    Form for agency owners to create a new agency account.
    Collects both User and Agency information.
    """

    # Agency-specific fields
    agency_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter agency name",
                "id": "id_agency_name",
            }
        ),
    )
    agency_type = forms.ChoiceField(
        choices=AGENCY_TYPE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "id": "id_agency_type",
            }
        ),
    )
    agency_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter agency email",
                "id": "id_agency_email",
            }
        ),
    )
    agency_phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter agency phone number",
                "id": "id_agency_phone_number",
            }
        ),
    )
    agency_website = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter agency website URL",
                "id": "id_agency_website",
            }
        ),
    )

    # Address fields
    address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control address-autocomplete",
                "placeholder": "Enter address line 1",
                "autocomplete": "address-line1",
                "id": "id_address_line1",
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
                "id": "id_address_line2",
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
                "id": "id_city",
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
                "id": "id_county",
            }
        ),
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        initial="UK",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter country",
                "readonly": "readonly",
                "autocomplete": "country-name",
                "id": "id_country",
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
                "id": "id_postcode",
            }
        ),
    )
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_latitude"}),
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_longitude"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter username",
                    "id": "id_username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email",
                    "id": "id_email",
                }
            ),
            "password1": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter password",
                    "id": "id_password1",
                }
            ),
            "password2": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Confirm password",
                    "id": "id_password2",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your first name",
                    "id": "id_first_name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your last name",
                    "id": "id_last_name",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(AgencySignUpForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "username",
            "email",
            Row(
                Column("password1", css_class="form-group col-md-6 mb-0"),
                Column("password2", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            "agency_name",
            "agency_type",
            "address_line1",
            "address_line2",
            Row(
                Column("city", css_class="form-group col-md-4 mb-0"),
                Column("county", css_class="form-group col-md-4 mb-0"),
                Column("postcode", css_class="form-group col-md-4 mb-0"),
            ),
            "country",
            "agency_email",
            "agency_phone_number",
            "agency_website",
            # Hidden fields
            Field("latitude"),
            Field("longitude"),
        )

    def clean_email(self):
        """
        Ensures the email is valid and not already in use.
        """
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        # Validate email format
        try:
            forms.EmailField().clean(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_travel_radius(self):
        """
        Ensures that travel_radius defaults to 0.0 if not provided.
        """
        travel_radius = self.cleaned_data.get("travel_radius")
        if travel_radius is None:
            return 0.0
        if travel_radius < 0 or travel_radius > 50:
            raise ValidationError("Travel radius must be between 0 and 50 miles.")
        return travel_radius


def clean_postcode(self):
    """
    Validates the postcode based on UK-specific formats.
    """
    postcode = self.cleaned_data.get("postcode", "")
    if postcode:
        postcode = postcode.strip()

    # Handle empty postcode case
    if not postcode:
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

    def clean(self):
        """
        Clean method to perform geocoding of the address.
        """
        cleaned_data = super().clean()
        address_line1 = cleaned_data.get("address_line1")
        address_line2 = cleaned_data.get("address_line2")
        city = cleaned_data.get("city")
        county = cleaned_data.get("county")
        postcode = cleaned_data.get("postcode")
        country = cleaned_data.get("country")

        # Construct the full address
        address_components = [
            address_line1,
            address_line2,
            city,
            county,
            postcode,
            country,
        ]
        full_address = ", ".join(filter(None, address_components))

        if full_address.strip():
            try:
                geocode_result = geocode_address(full_address)
                cleaned_data["latitude"] = geocode_result["latitude"]
                cleaned_data["longitude"] = geocode_result["longitude"]
                logger.info(f"Geocoded address for agency signup: {full_address}")
            except Exception as e:
                logger.error(f"Failed to geocode address for agency signup: {e}")
                self.add_error(None, "Invalid address. Please enter a valid address.")
        else:
            self.add_error("address_line1", "Address fields cannot be empty.")
        return cleaned_data

    def save(self, commit=True):
        """
        Saves the User and Agency instances.
        """
        # Save User
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.role = "agency_owner"

        if commit:
            user.save()
            # Assign user to 'Agency Owners' group
            assign_user_to_group(user, "Agency Owners")

            # Create Agency
            agency = Agency.objects.create(
                name=self.cleaned_data["agency_name"],
                agency_type=self.cleaned_data["agency_type"],
                postcode=self.cleaned_data.get("postcode"),
                address_line1=self.cleaned_data.get("address_line1"),
                address_line2=self.cleaned_data.get("address_line2"),
                city=self.cleaned_data.get("city"),
                county=self.cleaned_data.get("county"),
                country=self.cleaned_data.get("country") or "UK",
                email=self.cleaned_data["agency_email"],
                phone_number=self.cleaned_data.get("agency_phone_number"),
                website=self.cleaned_data.get("agency_website"),
                latitude=self.cleaned_data.get("latitude"),
                longitude=self.cleaned_data.get("longitude"),
                owner=user,
            )

            # Update Profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.agency = agency
            profile.address_line1 = self.cleaned_data.get("address_line1")
            profile.address_line2 = self.cleaned_data.get("address_line2")
            profile.city = self.cleaned_data.get("city")
            profile.county = self.cleaned_data.get("county")
            profile.country = self.cleaned_data.get("country") or "UK"
            profile.postcode = self.cleaned_data.get("postcode")
            profile.latitude = self.cleaned_data.get("latitude")
            profile.longitude = self.cleaned_data.get("longitude")
            profile.travel_radius = self.cleaned_data.get("travel_radius") or 0.0
            profile.save()

            # Log the creation
            logger.info(
                f"New agency owner created: {user.username}, Agency: {agency.name}"
            )

        return user


class SignUpForm(AddressFormMixin, UserCreationForm):
    """
    Form for users to sign up (primarily via invitation).
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
                "required": True,
                "id": "id_email",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your first name",
                "id": "id_first_name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your last name",
                "id": "id_last_name",
            }
        ),
    )
    travel_radius = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter travel radius (in miles)",
                "id": "id_travel_radius",
            }
        ),
    )

    # Address fields
    address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control address-autocomplete",
                "placeholder": "Enter address line 1",
                "autocomplete": "address-line1",
                "id": "id_address_line1",
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
                "id": "id_address_line2",
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
                "id": "id_city",
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
                "id": "id_county",
            }
        ),
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        initial="UK",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter country",
                "readonly": "readonly",
                "autocomplete": "country-name",
                "id": "id_country",
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
                "id": "id_postcode",
            }
        ),
    )
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_latitude"}),
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_longitude"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter username",
                    "id": "id_username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        # Accept 'request' as a keyword argument to access the current user
        self.request = kwargs.pop("request", None)
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("username", css_class="form-group col-md-6 mb-0"),
                Column("email", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("password1", css_class="form-group col-md-6 mb-0"),
                Column("password2", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            "travel_radius",
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

    def clean_email(self):
        """
        Ensures the email is valid and not already in use.
        """
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        # Validate email format
        try:
            forms.EmailField().clean(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_travel_radius(self):
        """
        Ensures that travel_radius defaults to 0.0 if not provided.
        """
        travel_radius = self.cleaned_data.get("travel_radius")
        if travel_radius is None:
            return 0.0
        if travel_radius < 0 or travel_radius > 50:
            raise ValidationError("Travel radius must be between 0 and 50 miles.")
        return travel_radius

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

    def clean(self):
        """
        Clean method to perform geocoding of the address.
        """
        cleaned_data = super().clean()
        address_line1 = cleaned_data.get("address_line1")
        address_line2 = cleaned_data.get("address_line2")
        city = cleaned_data.get("city")
        county = cleaned_data.get("county")
        postcode = cleaned_data.get("postcode")
        country = cleaned_data.get("country")

        # Construct the full address
        address_components = [
            address_line1,
            address_line2,
            city,
            county,
            postcode,
            country,
        ]
        full_address = ", ".join(filter(None, address_components))

        if full_address.strip():
            try:
                geocode_result = geocode_address(full_address)
                cleaned_data["latitude"] = geocode_result["latitude"]
                cleaned_data["longitude"] = geocode_result["longitude"]
                logger.info(f"Geocoded address for user signup: {full_address}")
            except Exception as e:
                logger.error(f"Failed to geocode address for user signup: {e}")
                self.add_error(None, "Invalid address. Please enter a valid address.")
        else:
            self.add_error("address_line1", "Address fields cannot be empty.")
        return cleaned_data

    def save(self, commit=True):
        """
        Saves the user and associates them with the 'Agency Staff' group and their agency.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "").strip().lower()

        user.role = "staff"

        if commit:
            user.save()
            # Assign user to 'Agency Staff' group
            assign_user_to_group(user, "Agency Staff")

            # Associate user with the agency if available
            if (
                self.request
                and hasattr(self.request.user, "profile")
                and self.request.user.profile.agency
            ):
                agency = self.request.user.profile.agency
                profile, created = Profile.objects.get_or_create(user=user)
                profile.agency = agency
                profile.travel_radius = self.cleaned_data.get("travel_radius") or 0.0
                profile.address_line1 = self.cleaned_data.get("address_line1")
                profile.address_line2 = self.cleaned_data.get("address_line2")
                profile.city = self.cleaned_data.get("city")
                profile.county = self.cleaned_data.get("county")
                profile.country = self.cleaned_data.get("country") or "UK"
                profile.postcode = self.cleaned_data.get("postcode")
                profile.latitude = self.cleaned_data.get("latitude")
                profile.longitude = self.cleaned_data.get("longitude")
                profile.save()
            else:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.travel_radius = self.cleaned_data.get("travel_radius") or 0.0
                profile.save()

            # Log the creation of a new user
            logger.info(f"New user created: {user.username}")

        return user


class InvitationForm(forms.ModelForm):
    """
    Form for agency managers to invite new staff members via email.
    Superusers can also select an agency.
    """

    class Meta:
        model = Invitation
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter staff email",
                    "required": True,
                    "id": "id_email",
                }
            ),
        }

    # Add agency field only if the user is a superuser
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(InvitationForm, self).__init__(*args, **kwargs)
        if user and user.is_superuser:
            self.fields["agency"] = forms.ModelChoiceField(
                queryset=Agency.objects.all(),
                required=False,
                widget=forms.Select(attrs={"class": "form-control", "id": "id_agency"}),
                help_text="Select an agency for the staff member. Leave blank if not applicable.",
            )
        else:
            # For non-superusers, associate with their own agency
            if hasattr(user, "profile") and user.profile.agency:
                self.initial["agency"] = user.profile.agency

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "email",
            "agency",
        )

    def clean_email(self):
        """
        Validates the invitation email to prevent duplicates and existing users.
        """
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        if Invitation.objects.filter(email=email, is_active=True).exists():
            raise ValidationError("An active invitation for this email already exists.")
        return email


class AcceptInvitationForm(UserCreationForm):
    """
    Form for invited staff members to accept their invitation and set up their account.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "readonly": "readonly", "id": "id_email"}
        ),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a username",
                "id": "id_username",
            }
        ),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter password",
                "id": "id_password1",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm password",
                "id": "id_password2",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {}

    def __init__(self, *args, **kwargs):
        self.invitation = kwargs.pop("invitation", None)
        self.request = kwargs.pop("request", None)
        super(AcceptInvitationForm, self).__init__(*args, **kwargs)
        if self.invitation:
            self.fields["email"].initial = self.invitation.email
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "email",
            "username",
            Row(
                Column("password1", css_class="form-group col-md-6 mb-0"),
                Column("password2", css_class="form-group col-md-6 mb-0"),
            ),
        )

    def clean_email(self):
        """
        Ensures the email remains unchanged.
        """
        email = self.initial.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        return email

    def clean_travel_radius(self):
        """
        Ensures that travel_radius defaults to 0.0 if not provided.
        """
        travel_radius = self.cleaned_data.get("travel_radius")
        if travel_radius is None:
            return 0.0
        if travel_radius < 0 or travel_radius > 50:
            raise ValidationError("Travel radius must be between 0 and 50 miles.")
        return travel_radius

    def save(self, commit=True):
        """
        Saves the user, assigns to 'Agency Staff' group, and creates an associated Profile.
        """
        user = super().save(commit=False)
        user.email = self.initial.get("email", "").strip().lower()
        user.role = "staff"

        if commit:
            user.save()
            # Assign to 'Agency Staff' group
            assign_user_to_group(user, "Agency Staff")

            # Link the user to the agency associated with the invitation
            if self.invitation and self.invitation.agency:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.agency = self.invitation.agency
                profile.travel_radius = self.cleaned_data.get("travel_radius") or 0.0
                profile.address_line1 = self.cleaned_data.get("address_line1")
                profile.address_line2 = self.cleaned_data.get("address_line2")
                profile.city = self.cleaned_data.get("city")
                profile.county = self.cleaned_data.get("county")
                profile.country = self.cleaned_data.get("country") or "UK"
                profile.postcode = self.cleaned_data.get("postcode")
                profile.latitude = self.cleaned_data.get("latitude")
                profile.longitude = self.cleaned_data.get("longitude")
                profile.save()

            # Mark the invitation as used
            if self.invitation:
                self.invitation.is_active = False
                self.invitation.accepted_at = timezone.now()
                self.invitation.save()

            # Log the acceptance of the invitation
            logger.info(f"Invitation accepted by user: {user.username}")

            # Log the user in
            if self.request:
                login(self.request, user)

        return user


class ProfilePictureForm(forms.ModelForm):
    """
    Form for uploading and updating the profile picture.
    """

    class Meta:
        model = Profile
        fields = ["profile_picture"]
        widgets = {
            "profile_picture": forms.ClearableFileInput(
                attrs={
                    "class": "form-control-file",
                    "id": "id_profile_picture",
                }
            ),
        }

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture", False)
        if picture:
            # Validate file size
            max_file_size = 5 * 1024 * 1024  # Set maximum file size to 5MB
            if picture.size > max_file_size:
                logger.warning(f"Profile picture size too large: {picture.size} bytes.")
                raise ValidationError("Image file too large ( > 5MB ).")

            # Validate content type using Pillow
            try:
                img = Image.open(picture)
                img_format = img.format.lower()
                if img_format not in ["jpeg", "png", "gif"]:
                    logger.warning(f"Unsupported image format: {img_format}.")
                    raise ValidationError(
                        "Unsupported file type. Only JPEG, PNG, and GIF are allowed."
                    )

            except ValidationError as ve:
                # Re-raise validation errors
                raise ve
            except Exception as e:
                logger.error(f"Error processing profile picture: {e}")
                raise ValidationError("Invalid image file.")
        else:
            logger.debug("No profile picture uploaded.")
        return picture


class UpdateProfileForm(AddressFormMixin, forms.ModelForm):
    """
    Form for users to update their profile information (excluding profile picture).
    """

    class Meta:
        model = Profile
        fields = [
            "address_line1",
            "address_line2",
            "city",
            "county",
            "country",
            "postcode",
            "travel_radius",
            "latitude",
            "longitude",
        ]
        widgets = {
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
            "travel_radius": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "placeholder": "Travel Radius (miles)",
                    "id": "id_travel_radius",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "address_line1",
            "address_line2",
            Row(
                Column("city", css_class="form-group col-md-4 mb-0"),
                Column("county", css_class="form-group col-md-4 mb-0"),
                Column("postcode", css_class="form-group col-md-4 mb-0"),
            ),
            "country",
            "travel_radius",
            # Hidden fields
            Field("latitude"),
            Field("longitude"),
        )

    def __init__(self, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "address_line1",
            "address_line2",
            Row(
                Column("city", css_class="form-group col-md-4 mb-0"),
                Column("county", css_class="form-group col-md-4 mb-0"),
                Column("postcode", css_class="form-group col-md-4 mb-0"),
            ),
            Row(
                Column("country", css_class="form-group col-md-6 mb-0"),
            ),
            "travel_radius",
            # Hidden fields
            Field("latitude"),
            Field("longitude"),
        )


    def clean_postcode(self):
        """
        Validates the postcode based on UK-specific formats.
        """
        postcode = self.cleaned_data.get("postcode", "")
        if postcode:
            postcode = postcode.strip()

        # Handle empty postcode case
        if not postcode:
            return postcode

        # UK postcode regex
        uk_postcode_regex = r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$"
        if not re.match(uk_postcode_regex, postcode.upper()):
            raise ValidationError("Enter a valid UK postcode.")
        return postcode.upper()

    def clean_travel_radius(self):
        """
        Ensures that travel_radius defaults to 0.0 if not provided.
        """
        travel_radius = self.cleaned_data.get("travel_radius")
        if travel_radius is None:
            return 0.0
        if travel_radius < 0 or travel_radius > 50:
            raise ValidationError("Travel radius must be between 0 and 50 miles.")
        return travel_radius

    def clean(self):
        """
        Clean method to perform geocoding of the address.
        """
        cleaned_data = super().clean()
        address_line1 = cleaned_data.get("address_line1")
        address_line2 = cleaned_data.get("address_line2")
        city = cleaned_data.get("city")
        county = cleaned_data.get("county")
        postcode = cleaned_data.get("postcode")
        country = cleaned_data.get("country")

        # Construct the full address
        address_components = [
            address_line1,
            address_line2,
            city,
            county,
            postcode,
            country,
        ]
        full_address = ", ".join(filter(None, address_components))

        if full_address.strip():
            try:
                geocode_result = geocode_address(full_address)
                cleaned_data["latitude"] = geocode_result["latitude"]
                cleaned_data["longitude"] = geocode_result["longitude"]
                logger.info(f"Geocoded address for profile update: {full_address}")
            except Exception as e:
                logger.error(f"Failed to geocode address for profile update: {e}")
                self.add_error(None, "Invalid address. Please enter a valid address.")
        else:
            self.add_error("address_line1", "Address fields cannot be empty.")
        return cleaned_data

    def save(self, commit=True):
        """
        Override save method to update Profile.
        """
        profile = super().save(commit=False)
        if commit:
            profile.save()
        return profile


class UserForm(UserCreationForm):
    """
    Form for creating users via Class-Based Views.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter email",
                "required": True,
                "id": "id_email",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter first name",
                "id": "id_first_name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter last name",
                "id": "id_last_name",
            }
        ),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_group"}),
        label="Group",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "group",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter username",
                    "id": "id_username",
                }
            ),
            "password1": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter password",
                    "id": "id_password1",
                }
            ),
            "password2": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Confirm password",
                    "id": "id_password2",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("username", css_class="form-group col-md-6 mb-0"),
                Column("email", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            "group",
            Row(
                Column("password1", css_class="form-group col-md-6 mb-0"),
                Column("password2", css_class="form-group col-md-6 mb-0"),
            ),
        )

    def clean_email(self):
        """
        Ensures the email is unique.
        """
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class UserUpdateForm(UserChangeForm):
    """
    Form for updating users via Class-Based Views without changing the password.
    """

    password = None  # Exclude the password field

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter email",
                "required": True,
                "id": "id_email",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter first name",
                "id": "id_first_name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter last name",
                "id": "id_last_name",
            }
        ),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_group"}),
        label="Group",
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_is_active",
            }
        ),
        label="Is Active",
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "group", "is_active")
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter username",
                    "id": "id_username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("email", css_class="form-group col-md-6 mb-0"),
                Column("is_active", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            "group",
            "username",
        )

    def clean_email(self):
        """
        Ensures the email remains unique.
        """
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class StaffCreationForm(AddressFormMixin, UserCreationForm):
    """
    Form for agency managers to add new staff members.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter staff email",
                "required": True,
                "id": "id_email",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter staff first name",
                "id": "id_first_name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter staff last name",
                "id": "id_last_name",
            }
        ),
    )
    travel_radius = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter travel radius (in miles)",
                "id": "id_travel_radius",
            }
        ),
    )

    # Address fields
    address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control address-autocomplete",
                "placeholder": "Enter address line 1",
                "autocomplete": "address-line1",
                "id": "id_address_line1",
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
                "id": "id_address_line2",
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
                "id": "id_city",
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
                "id": "id_county",
            }
        ),
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        initial="UK",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter country",
                "readonly": "readonly",
                "autocomplete": "country-name",
                "id": "id_country",
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
                "id": "id_postcode",
            }
        ),
    )
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_latitude"}),
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_longitude"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter username",
                    "id": "id_username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(StaffCreationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("username", css_class="form-group col-md-6 mb-0"),
                Column("email", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("password1", css_class="form-group col-md-6 mb-0"),
                Column("password2", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            "travel_radius",
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

    def clean_email(self):
        """
        Validates the email to prevent duplicates and existing users.
        """
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        if Invitation.objects.filter(email=email, is_active=True).exists():
            raise ValidationError("An active invitation for this email already exists.")
        return email

    def clean_travel_radius(self):
        """
        Ensures that travel_radius defaults to 0.0 if not provided.
        """
        travel_radius = self.cleaned_data.get("travel_radius")
        if travel_radius is None:
            return 0.0
        if travel_radius < 0 or travel_radius > 50:
            raise ValidationError("Travel radius must be between 0 and 50 miles.")
        return travel_radius


    def clean_postcode(self):
        """
        Validates the postcode based on UK-specific formats.
        """
        postcode = self.cleaned_data.get("postcode", "")
        if postcode:
            postcode = postcode.strip()

        # Handle empty postcode case
        if not postcode:
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

    def clean(self):
        """
        Clean method to perform geocoding of the address.
        """
        cleaned_data = super().clean()
        address_line1 = cleaned_data.get("address_line1")
        address_line2 = cleaned_data.get("address_line2")
        city = cleaned_data.get("city")
        county = cleaned_data.get("county")
        postcode = cleaned_data.get("postcode")
        country = cleaned_data.get("country")

        # Construct the full address
        address_components = [
            address_line1,
            address_line2,
            city,
            county,
            postcode,
            country,
        ]
        full_address = ", ".join(filter(None, address_components))

        if full_address.strip():
            try:
                geocode_result = geocode_address(full_address)
                cleaned_data["latitude"] = geocode_result["latitude"]
                cleaned_data["longitude"] = geocode_result["longitude"]
                logger.info(
                    f"Geocoded address for invitation acceptance: {full_address}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to geocode address for invitation acceptance: {e}"
                )
                self.add_error(None, "Invalid address. Please enter a valid address.")
        else:
            self.add_error("address_line1", "Address fields cannot be empty.")
        return cleaned_data

    def save(self, commit=True):
        """
        Saves the user, assigns to 'Agency Staff' group, and creates an associated Profile.
        """
        user = super().save(commit=False)
        user.email = self.initial.get("email", "").strip().lower()
        user.role = "staff"

        if commit:
            user.save()
            # Assign to 'Agency Staff' group
            assign_user_to_group(user, "Agency Staff")

            # Associate user with the agency if available
            if (
                self.request
                and hasattr(self.request.user, "profile")
                and self.request.user.profile.agency
            ):
                agency = self.request.user.profile.agency
                profile, created = Profile.objects.get_or_create(user=user)
                profile.agency = agency
                profile.travel_radius = self.cleaned_data.get("travel_radius") or 0.0
                profile.address_line1 = self.cleaned_data.get("address_line1")
                profile.address_line2 = self.cleaned_data.get("address_line2")
                profile.city = self.cleaned_data.get("city")
                profile.county = self.cleaned_data.get("county")
                profile.country = self.cleaned_data.get("country") or "UK"
                profile.postcode = self.cleaned_data.get("postcode")
                profile.latitude = self.cleaned_data.get("latitude")
                profile.longitude = self.cleaned_data.get("longitude")
                profile.save()
            else:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.travel_radius = self.cleaned_data.get("travel_radius") or 0.0
                profile.save()

            # Log the creation of a new user
            logger.info(f"New staff member created: {user.username}")

        return user


class StaffUpdateForm(AddressFormMixin, forms.ModelForm):
    """
    Form for agency managers to update existing staff members.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter email",
                "required": True,
                "id": "id_email",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter first name",
                "id": "id_first_name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter last name",
                "id": "id_last_name",
            }
        ),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_is_active",
            }
        ),
        label="Is Active",
    )
    travel_radius = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter travel radius (in miles)",
                "id": "id_travel_radius",
            }
        ),
    )

    # Address fields
    address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control address-autocomplete",
                "placeholder": "Enter address line 1",
                "autocomplete": "address-line1",
                "id": "id_address_line1",
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
                "id": "id_address_line2",
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
                "id": "id_city",
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
                "id": "id_county",
            }
        ),
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        initial="UK",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter country",
                "readonly": "readonly",
                "autocomplete": "country-name",
                "id": "id_country",
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
                "id": "id_postcode",
            }
        ),
    )
    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_latitude"}),
    )
    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_longitude"}),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "is_active")
        widgets = {}

    def __init__(self, *args, **kwargs):
        super(StaffUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("email", css_class="form-group col-md-6 mb-0"),
                Column("is_active", css_class="form-group col-md-6 mb-0"),
            ),
            Row(
                Column("first_name", css_class="form-group col-md-6 mb-0"),
                Column("last_name", css_class="form-group col-md-6 mb-0"),
            ),
            "travel_radius",
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

    def clean_email(self):
        """
        Ensures the email remains unique.
        """
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_travel_radius(self):
        """
        Ensures that travel_radius defaults to 0.0 if not provided.
        """
        travel_radius = self.cleaned_data.get("travel_radius")
        if travel_radius is None:
            return 0.0
        if travel_radius < 0 or travel_radius > 50:
            raise ValidationError("Travel radius must be between 0 and 50 miles.")
        return travel_radius


    def clean_postcode(self):
        """
        Validates the postcode based on UK-specific formats.
        """
        postcode = self.cleaned_data.get("postcode", "")
        if postcode:
            postcode = postcode.strip()

        # Handle empty postcode case
        if not postcode:
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

    def clean(self):
        """
        Clean method to perform geocoding of the address.
        """
        cleaned_data = super().clean()
        address_line1 = cleaned_data.get("address_line1")
        address_line2 = cleaned_data.get("address_line2")
        city = cleaned_data.get("city")
        county = cleaned_data.get("county")
        postcode = cleaned_data.get("postcode")
        country = cleaned_data.get("country")

        # Construct the full address
        address_components = [
            address_line1,
            address_line2,
            city,
            county,
            postcode,
            country,
        ]
        full_address = ", ".join(filter(None, address_components))

        if full_address.strip():
            try:
                geocode_result = geocode_address(full_address)
                cleaned_data["latitude"] = geocode_result["latitude"]
                cleaned_data["longitude"] = geocode_result["longitude"]
                logger.info(f"Geocoded address for staff update: {full_address}")
            except Exception as e:
                logger.error(f"Failed to geocode address for staff update: {e}")
                self.add_error(None, "Invalid address. Please enter a valid address.")
        else:
            self.add_error("address_line1", "Address fields cannot be empty.")
        return cleaned_data

    def save(self, commit=True):
        """
        Saves the user and updates the associated Profile.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "").strip().lower()

        if commit:
            user.save()
            # Update profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.travel_radius = self.cleaned_data.get("travel_radius") or 0.0
            profile.save()

            # Log the update
            logger.info(f"Staff member updated: {user.username}")

        return user


class ActivateTOTPForm(forms.Form):
    totp_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter code from authenticator",
                "id": "id_totp_code",
            }
        ),
        label="Enter TOTP Code",
    )


class RecoveryCodeForm(forms.Form):
    recovery_code = forms.CharField(
        max_length=8,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Recovery Code",
                "id": "id_recovery_code",
            }
        ),
        label="Recovery Code",
    )


class MFAForm(forms.Form):
    totp_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter MFA code",
                "id": "id_totp_code",
            }
        ),
        label="MFA Code",
    )
