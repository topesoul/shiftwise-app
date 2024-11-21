# /workspace/shiftwise/accounts/forms.py

import logging
import re
import uuid

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row
from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.constants import ROLE_CHOICES, AGENCY_TYPE_CHOICES
from core.forms import AddressFormMixin
from core.utils import assign_user_to_group, generate_unique_code

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
            "address_line1",
            "address_line2",
            "city",
            "county",
            "state",
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
                choices=AGENCY_TYPE_CHOICES,
                attrs={"class": "form-control", "id": "id_agency_type"},
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
        }

    def __init__(self, *args, **kwargs):
        super(AgencyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("name", css_class="form-group col-md-6 mb-0"),
            ),
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
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter your first name"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter your last name"}
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
            }
        ),
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
                }
            ),
            # Hidden fields for latitude and longitude are already handled by AddressFormMixin
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
                profile.travel_radius = self.cleaned_data.get("travel_radius", 0)
                profile.latitude = self.cleaned_data.get("latitude")
                profile.longitude = self.cleaned_data.get("longitude")
                profile.save()
            else:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.save()

            # Log the creation of a new user
            logger.info(f"New user created: {user.username}")

        return user


class AgencySignUpForm(AddressFormMixin, UserCreationForm):
    """
    Form for agency managers to create a new agency account.
    """

    # Agency fields are now handled by AddressFormMixin
    agency_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter agency name",
                "required": True,
                "id": "id_agency_name",
            }
        ),
    )
    agency_type = forms.ChoiceField(
        choices=AGENCY_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_agency_type"}),
    )
    agency_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter agency email",
                "required": True,
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
                "id": "id_phone_number",
            }
        ),
    )
    agency_website = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter agency website URL",
                "id": "id_website",
            }
        ),
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
                }
            ),
            # Hidden fields for latitude and longitude are already handled by AddressFormMixin
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
        email = (self.cleaned_data.get("email") or '').strip().lower()
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

    def clean_agency_email(self):
        """
        Ensures the agency email is valid and not already in use.
        """
        agency_email = (self.cleaned_data.get("agency_email") or '').strip().lower()
        if not agency_email:
            raise ValidationError("Agency email is required.")
        try:
            forms.EmailField().clean(agency_email)
        except ValidationError:
            raise ValidationError("Enter a valid agency email address.")
        if User.objects.filter(email=agency_email).exists():
            raise ValidationError("A user with this agency email already exists.")
        return agency_email

    def save(self, commit=True):
        """
        Saves the user and creates an associated Agency and Profile.
        Auto-generates the agency_code using a utility function.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.role = "agency_manager"

        if commit:
            user.save()

            # Create Agency with auto-generated agency_code using utility function
            agency = Agency.objects.create(
                name=self.cleaned_data["agency_name"],
                agency_type=self.cleaned_data["agency_type"],
                postcode=self.cleaned_data.get("postcode"),
                address_line1=self.cleaned_data.get("address_line1"),
                address_line2=self.cleaned_data.get("address_line2"),
                city=self.cleaned_data.get("city"),
                county=self.cleaned_data.get("county"),
                state=self.cleaned_data.get("state"),
                country=self.cleaned_data.get("country") or "UK",
                email=self.cleaned_data["agency_email"],
                phone_number=self.cleaned_data.get("agency_phone_number"),
                website=self.cleaned_data.get("agency_website"),
                latitude=self.cleaned_data.get("latitude"),
                longitude=self.cleaned_data.get("longitude"),
                owner=user,
            )

            # Assign user to 'Agency Managers' group
            assign_user_to_group(user, "Agency Managers")

            # Assign user to 'Agency Owners' group
            assign_user_to_group(user, "Agency Owners")

            # Associate user with the agency and update profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.agency = agency
            profile.latitude = self.cleaned_data.get("latitude")
            profile.longitude = self.cleaned_data.get("longitude")
            profile.save()

            # Log the creation of a new agency manager
            logger.info(
                f"New agency manager created: {user.username}, Agency: {agency.name}"
            )

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
                widget=forms.Select(attrs={"class": "form-control"}),
                help_text="Select an agency for the staff member. Leave blank if not applicable.",
            )
        else:
            # For non-superusers, associate with their own agency
            if hasattr(user, "profile") and user.profile.agency:
                self.initial["agency"] = user.profile.agency

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
            attrs={"class": "form-control", "readonly": "readonly"}
        ),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a username",
                "required": True,
            }
        ),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter password",
                "required": True,
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm password",
                "required": True,
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

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
            # Address fields are handled by AddressFormMixin if needed
        )

    def clean_email(self):
        """
        Ensures the email remains unchanged.
        """
        email = self.initial.get("email", "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        return email

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

            # Link the user to the agency associated with the invitation if applicable
            if self.invitation and self.invitation.agency:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.agency = self.invitation.agency
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
                    "id": "id_profile_picture"
                }
            ),
        }

    def clean_profile_picture(self):
        """
        Validates the uploaded profile picture.
        """
        picture = self.cleaned_data.get("profile_picture", False)
        if picture:
            if picture.size > 2 * 1024 * 1024:
                raise ValidationError("Image file too large ( > 2MB ).")
            content_type = picture.content_type
            if content_type not in ["image/jpeg", "image/png", "image/gif"]:
                raise ValidationError(
                    "Unsupported file type. Only JPEG, PNG, and GIF are allowed."
                )
            # Validate image dimensions
            from PIL import Image
            try:
                img = Image.open(picture)
                max_width, max_height = 2000, 2000  # Example limits
                if img.width > max_width or img.height > max_height:
                    raise ValidationError(
                        f"Image dimensions should not exceed {max_width}x{max_height} pixels."
                    )
            except Exception:
                raise ValidationError("Invalid image file.")
        else:
            # Make profile picture optional; no error if not provided
            pass
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
            "state",
            "country",
            "postcode",
            "travel_radius",
            "latitude",
            "longitude",
        ]
        widgets = {
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
            Row(
                Column("state", css_class="form-group col-md-6 mb-0"),
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
        postcode = self.cleaned_data.get("postcode", "").strip()
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
                "required": True,
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
                "required": True,
            }
        ),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
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
                }
            ),
            "password1": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter password",
                }
            ),
            "password2": forms.PasswordInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Confirm password",
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
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter first name",
                "required": True,
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter last name",
                "required": True,
            }
        ),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "group", "is_active")
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter username",
                }
            ),
            # Hidden fields for address are handled in UpdateProfileForm
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
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter staff first name"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter staff last name"}
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
            }
        ),
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
                }
            ),
            # Hidden fields for latitude and longitude are already handled by AddressFormMixin
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

    def save(self, commit=True):
        """
        Saves the user, assigns to 'Agency Staff' group, and creates an associated Profile.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "").strip().lower()
        user.role = "staff"

        if commit:
            user.save()
            assign_user_to_group(user, "Agency Staff")

            if (
                self.request
                and hasattr(self.request.user, "profile")
                and self.request.user.profile.agency
            ):
                agency = self.request.user.profile.agency
                profile, created = Profile.objects.get_or_create(user=user)
                profile.agency = agency
                profile.travel_radius = self.cleaned_data.get("travel_radius", 0)
                profile.save()
            else:
                profile, created = Profile.objects.get_or_create(user=user)
                profile.travel_radius = self.cleaned_data.get("travel_radius", 0)
                profile.save()

            # Log the creation of a new staff member
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
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter first name",
                "required": True,
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter last name",
                "required": True,
            }
        ),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
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
            }
        ),
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
        Validates the travel radius value.
        """
        travel_radius = self.cleaned_data.get("travel_radius")
        if travel_radius is not None:
            if travel_radius < 0 or travel_radius > 50:
                raise ValidationError("Travel radius must be between 0 and 50 miles.")
        return travel_radius

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
            profile.travel_radius = self.cleaned_data.get(
                "travel_radius", profile.travel_radius
            )
            profile.save()

            # Log the update
            logger.info(f"Staff member updated: {user.username}")

        return user


class ActivateTOTPForm(forms.Form):
    totp_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter code from authenticator'}
        ),
        label="Enter TOTP Code",
    )


class RecoveryCodeForm(forms.Form):
    recovery_code = forms.CharField(max_length=8, required=True, label="Recovery Code")


class MFAForm(forms.Form):
    totp_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter MFA code'}),
        label='MFA Code',
    )