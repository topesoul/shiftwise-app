# /workspace/shiftwise/accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Profile
from shifts.models import Agency

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create Profile
            Profile.objects.create(user=user)
        return user

class ProfileForm(forms.ModelForm):
    agency = forms.ModelChoiceField(queryset=Agency.objects.filter(is_active=True), required=False)

    class Meta:
        model = Profile
        fields = ['agency']

class AgencySignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    agency_name = forms.CharField(max_length=100)
    agency_postcode = forms.CharField(max_length=10)
    agency_address_line1 = forms.CharField(max_length=255)
    agency_city = forms.CharField(max_length=100)
    agency_state = forms.CharField(max_length=100, required=False)
    agency_country = forms.CharField(max_length=100, required=False)
    agency_phone_number = forms.CharField(max_length=20, required=False)
    agency_website = forms.URLField(required=False)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password1', 'password2',
            'agency_name', 'agency_postcode', 'agency_address_line1',
            'agency_city', 'agency_state', 'agency_country',
            'agency_phone_number', 'agency_website'
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'agency_manager'
        if commit:
            user.save()
            # Create Agency
            agency = Agency.objects.create(
                name=self.cleaned_data['agency_name'],
                postcode=self.cleaned_data['agency_postcode'],
                address_line1=self.cleaned_data['agency_address_line1'],
                city=self.cleaned_data['agency_city'],
                state=self.cleaned_data.get('agency_state'),
                country=self.cleaned_data.get('agency_country'),
                phone_number=self.cleaned_data.get('agency_phone_number'),
                website=self.cleaned_data.get('agency_website'),
            )
            # Assign user to 'Agency Managers' group
            agency_managers_group, created = Group.objects.get_or_create(name='Agency Managers')
            user.groups.add(agency_managers_group)
            # Associate user with the agency
            Profile.objects.create(user=user, agency=agency)
        return user
