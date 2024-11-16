# /workspace/shiftwise/accounts/views.py

import logging
import pyotp
import qrcode
import base64
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.models import Group
from django.views.generic import (
    UpdateView,
    DeleteView,
    CreateView,
    ListView,
    View,
    FormView,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

from .forms import (
    SignUpForm,
    AgencySignUpForm,
    InvitationForm,
    AcceptInvitationForm,
    UpdateProfileForm,
    AgencyForm,
    UserForm,
    UserUpdateForm,
)
from .models import Profile, Invitation, Agency
from shifts.models import ShiftAssignment, Shift
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from shiftwise.utils import get_address_from_address_line1
from subscriptions.models import Subscription

# Import mixins from core.mixins
from core.mixins import (
    SuperuserRequiredMixin,
    AgencyOwnerRequiredMixin,
    AgencyManagerRequiredMixin,
    AgencyStaffRequiredMixin,
    SubscriptionRequiredMixin,
)

User = get_user_model()

# Initialize the logger
logger = logging.getLogger(__name__)

# ---------------------------
# Authentication CBVs
# ---------------------------


class LoginView(FormView):
    """Handles user login."""

    template_name = "accounts/login.html"
    form_class = AuthenticationForm
    success_url = reverse_lazy("home:home")  # Default redirect

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect based on role
            if request.user.is_superuser:
                return redirect("accounts:superuser_dashboard")
            elif request.user.groups.filter(name="Agency Managers").exists():
                return redirect("accounts:agency_dashboard")
            elif request.user.groups.filter(name="Agency Staff").exists():
                return redirect("accounts:staff_dashboard")
            else:
                return redirect("home:home")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        messages.success(self.request, f"Welcome back, {user.get_full_name()}!")
        logger.info(f"User {user.username} logged in successfully.")
        # Redirect based on role
        if user.is_superuser:
            logger.debug(f"Redirecting {user.username} to superuser_dashboard.")
            return redirect("accounts:superuser_dashboard")
        elif user.groups.filter(name="Agency Managers").exists():
            logger.debug(f"Redirecting {user.username} to agency_dashboard.")
            return redirect("accounts:agency_dashboard")
        elif user.groups.filter(name="Agency Staff").exists():
            logger.debug(f"Redirecting {user.username} to staff_dashboard.")
            return redirect("accounts:staff_dashboard")
        else:
            logger.debug(f"Redirecting {user.username} to home:home.")
            return redirect("home:home")  # Default redirection

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        logger.warning(
            f"Failed login attempt for username: {self.request.POST.get('username')}"
        )
        return self.render_to_response(self.get_context_data(form=form))


class LogoutView(LoginRequiredMixin, View):
    """Handles user logout."""

    def get(self, request, *args, **kwargs):
        logger.info(f"User {request.user.username} logged out.")
        logout(request)
        messages.success(request, "You have successfully logged out.")
        return redirect(reverse("home:home"))


class SignUpView(FormView):
    """Handles user signup via invitations."""

    template_name = "accounts/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("accounts:login_view")

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "Your account has been created successfully.")
        logger.info(f"New user {user.username} signed up.")
        return super().form_valid(form)


class SignupSelectionView(TemplateView):
    """
    Renders a page for users to choose their signup type.
    """

    template_name = "accounts/signup_selection.html"


class AgencySignUpView(CreateView):
    """Handles agency signup."""

    model = User
    form_class = AgencySignUpForm
    template_name = "accounts/agency_signup.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        user = form.save()
        # Assign user to Agency Owners group
        agency_owners_group, _ = Group.objects.get_or_create(name="Agency Owners")
        user.groups.add(agency_owners_group)
        logger.info(f"User {user.username} assigned to 'Agency Owners' group.")

        # Authenticate the user to get the backend
        username = form.cleaned_data.get("username")
        raw_password = form.cleaned_data.get("password1")
        user = authenticate(username=username, password=raw_password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, "Your agency account has been created.")
            logger.info(f"Agency account created for user {user.username}.")
            return redirect("accounts:profile")
        else:
            messages.error(
                self.request, "Authentication failed. Please try logging in."
            )
            logger.error(
                f"Authentication failed for newly created user {user.username}."
            )
            return redirect("accounts:login_view")


# ---------------------------
# MFA CBVs
# ---------------------------


class ActivateTOTPView(LoginRequiredMixin, View):
    """Activates TOTP-based MFA."""

    def get(self, request, *args, **kwargs):
        # Check if MFA is already enabled
        if request.user.profile.totp_secret:
            messages.info(request, "MFA is already enabled on your account.")
            return redirect("accounts:profile")

        # Generate a new TOTP secret key
        totp_secret = pyotp.random_base32()
        request.session["totp_secret"] = totp_secret  # Save in session

        totp = pyotp.TOTP(totp_secret, interval=settings.MFA_TOTP_PERIOD)

        # Generate provisioning URI for authenticator apps
        provisioning_uri = totp.provisioning_uri(
            name=request.user.email, issuer_name=settings.MFA_TOTP_ISSUER
        )

        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()

        context = {
            "qr_code_image": qr_code_image,
        }

        return render(request, "accounts/mfa/activate_totp.html", context)

    def post(self, request, *args, **kwargs):
        # Retrieve the TOTP code entered by the user
        code = request.POST.get("totp_code")
        totp_secret = request.session.get("totp_secret")  # Retrieve from session

        if not totp_secret:
            messages.error(request, "Session expired. Please try activating MFA again.")
            logger.warning(
                f"User {request.user.username} tried to activate MFA without a valid TOTP secret in session."
            )
            return redirect("accounts:activate_totp")

        totp = pyotp.TOTP(totp_secret, interval=settings.MFA_TOTP_PERIOD)

        if totp.verify(code):
            # Save the TOTP secret to the user's profile
            request.user.profile.totp_secret = totp_secret
            request.user.profile.save()

            # Generate Recovery Codes
            recovery_codes = request.user.profile.generate_recovery_codes()

            messages.success(
                request,
                "MFA has been successfully activated. Please save your recovery codes securely.",
            )
            logger.info(f"MFA activated for user {request.user.username}.")

            del request.session["totp_secret"]  # Remove from session

            # Return recovery codes to the template for display
            context = {
                "recovery_codes": recovery_codes,
            }

            return render(request, "accounts/mfa/recovery_codes.html", context)
        else:
            messages.error(request, "Invalid code. Please try again.")
            logger.warning(f"Invalid MFA code entered by user {request.user.username}.")
            # Reuse the same totp_secret to allow the user to try again
            provisioning_uri = totp.provisioning_uri(
                name=request.user.email, issuer_name=settings.MFA_TOTP_ISSUER
            )

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            img = qr.make_image(fill="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_code_image = base64.b64encode(buffer.getvalue()).decode()

            context = {
                "qr_code_image": qr_code_image,
            }
            return render(request, "accounts/mfa/activate_totp.html", context)


class VerifyTOTPView(LoginRequiredMixin, View):
    """Verifies TOTP code for MFA."""

    @ratelimit(key="user", rate="5/m", block=True)
    def post(self, request, *args, **kwargs):
        user_totp_secret = getattr(request.user.profile, "totp_secret", None)

        if user_totp_secret:
            totp = pyotp.TOTP(user_totp_secret, interval=settings.MFA_TOTP_PERIOD)
            code = request.POST.get("totp_code")

            if totp.verify(code):
                messages.success(request, "MFA verification successful!")
                logger.info(
                    f"MFA verification successful for user {request.user.username}."
                )
                return redirect("home:home")
            else:
                messages.error(request, "Invalid code. Please try again.")
                logger.warning(
                    f"Invalid MFA code entered by user {request.user.username}."
                )
        else:
            messages.error(request, "MFA is not enabled on your account.")
            logger.warning(
                f"User {request.user.username} attempted MFA verification without MFA enabled."
            )

        return render(request, "accounts/mfa/authenticate.html")


class DisableTOTPView(LoginRequiredMixin, View):
    """Disables TOTP-based MFA for the user."""

    def get(self, request, *args, **kwargs):
        return render(request, "accounts/mfa/deactivate_totp.html")

    def post(self, request, *args, **kwargs):
        request.user.profile.totp_secret = None
        request.user.profile.save()
        messages.success(request, "MFA has been disabled.")
        logger.info(f"MFA disabled for user {request.user.username}.")
        return redirect("accounts:profile")


class ResendTOTPCodeView(LoginRequiredMixin, View):
    """Resends or refreshes the TOTP QR code."""

    def get(self, request, *args, **kwargs):
        user_totp_secret = request.user.profile.totp_secret or pyotp.random_base32()
        totp = pyotp.TOTP(user_totp_secret, interval=settings.MFA_TOTP_PERIOD)

        # Generate provisioning URI again
        provisioning_uri = totp.provisioning_uri(
            name=request.user.email, issuer_name=settings.MFA_TOTP_ISSUER
        )

        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()

        # Save new TOTP secret if not already set
        if not request.user.profile.totp_secret:
            request.user.profile.totp_secret = user_totp_secret
            request.user.profile.save()

        context = {
            "qr_code_image": qr_code_image,
            "totp_secret": user_totp_secret,
        }

        return render(request, "accounts/mfa/reauthenticate.html", context)


# ---------------------------
# Profile and Dashboard CBVs
# ---------------------------


class ProfileView(LoginRequiredMixin, SubscriptionRequiredMixin, UpdateView):
    """Renders the user profile with upcoming and past shifts and handles profile updates."""

    model = Profile
    form_class = UpdateProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        # Ensure the user has a profile
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your profile has been updated successfully.")
        logger.info(f"Profile updated for user {self.request.user.username}.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        logger.warning(
            f"Profile update failed for user {self.request.user.username}: {form.errors}"
        )
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Fetch all shift assignments for the user
        assigned_shifts = ShiftAssignment.objects.filter(worker=user)
        assigned_shift_ids = list(assigned_shifts.values_list("shift_id", flat=True))

        # Fetch upcoming and past shifts for the user
        today = timezone.now().date()
        upcoming_shifts = (
            assigned_shifts.filter(shift__shift_date__gte=today)
            .select_related("shift")
            .order_by("shift__shift_date")
        )

        past_shifts = (
            assigned_shifts.filter(shift__shift_date__lt=today)
            .select_related("shift")
            .order_by("-shift__shift_date")
        )

        context.update(
            {
                "upcoming_shifts": upcoming_shifts,
                "past_shifts": past_shifts,
                "assigned_shift_ids": assigned_shift_ids,
            }
        )
        return context


class AgencyDashboardView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, View
):
    """Renders the agency manager's dashboard."""

    def get(self, request, *args, **kwargs):
        user = request.user

        # Allow superusers to access all agencies
        if user.is_superuser:
            agencies = Agency.objects.all()
        else:
            agency = user.profile.agency
            agencies = Agency.objects.filter(id=agency.id)

        # Fetch data specific to agency or all agencies for superusers
        shifts = ShiftAssignment.objects.filter(
            shift__agency__in=agencies
        ).select_related("shift", "worker")

        return render(
            request,
            "accounts/agency_dashboard.html",
            {
                "agencies": agencies,
                "shifts": shifts,
            },
        )


class StaffDashboardView(
    LoginRequiredMixin, AgencyStaffRequiredMixin, SubscriptionRequiredMixin, View
):
    """Renders the staff member's dashboard."""

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # Retrieve all shifts assigned to the user
        assignments = ShiftAssignment.objects.filter(worker=user).select_related(
            "shift"
        )
        assigned_shift_ids = assignments.values_list("shift_id", flat=True)

        # Filter upcoming and past shifts for display
        upcoming_shifts = assignments.filter(shift__shift_date__gte=today)
        past_shifts = assignments.filter(shift__shift_date__lt=today)

        return render(
            request,
            "accounts/staff_dashboard.html",
            {
                "user": user,
                "upcoming_shifts": upcoming_shifts,
                "past_shifts": past_shifts,
                "assigned_shift_ids": list(assigned_shift_ids),
            },
        )


class SuperuserDashboardView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """Renders the superuser's dashboard."""

    def get(self, request, *args, **kwargs):
        # Display all agencies and users
        agencies = Agency.objects.all()
        users = User.objects.all()

        context = {
            "agencies": agencies,
            "users": users,
        }
        return render(request, "accounts/superuser_dashboard.html", context)


# ---------------------------
# Invitation CBVs
# ---------------------------


class InviteStaffView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, FormView
):
    """Allows agency managers or superusers to invite staff members via email."""

    template_name = "accounts/invite_staff.html"
    form_class = InvitationForm
    success_url = reverse_lazy("shifts:staff_list")

    def form_valid(self, form):
        invitation = form.save(commit=False)
        invitation.invited_by = self.request.user
        # Assign agency if the user is not a superuser
        if not self.request.user.is_superuser:
            if (
                hasattr(self.request.user, "profile")
                and self.request.user.profile.agency
            ):
                invitation.agency = self.request.user.profile.agency
                logger.debug(f"Agency assigned to invitation: {invitation.agency.name}")
            else:
                messages.error(self.request, "You are not associated with any agency.")
                logger.error(
                    f"User {self.request.user.username} attempted to invite staff without an associated agency."
                )
                return redirect("accounts:profile")
        else:
            # Superusers can optionally assign an agency
            invitation.agency = form.cleaned_data.get("agency")
            if invitation.agency:
                logger.debug(
                    f"Agency {invitation.agency.name} assigned by superuser {self.request.user.username}"
                )
            else:
                logger.debug(
                    "Superuser is inviting staff without associating to an agency."
                )

        invitation.save()
        logger.info(
            f"Invitation created: {invitation.email} by {self.request.user.username}"
        )

        # Prepare the email context
        invite_link = self.request.build_absolute_uri(
            reverse("accounts:accept_invitation", kwargs={"token": invitation.token})
        )
        agency_name = invitation.agency.name if invitation.agency else "ShiftWise"
        context = {
            "agency_name": agency_name,
            "invite_link": invite_link,
        }
        subject = "ShiftWise Staff Invitation"
        message = render_to_string("accounts/email/invite_staff_email.txt", context)

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [invitation.email],
                fail_silently=False,
            )
            messages.success(self.request, f"Invitation sent to {invitation.email}.")
            logger.info(
                f"Invitation email sent to {invitation.email} by {self.request.user.username}"
            )
        except Exception as e:
            messages.error(
                self.request, "Failed to send invitation email. Please try again later."
            )
            logger.exception(
                f"Failed to send invitation email to {invitation.email}: {e}"
            )
            # Optionally, delete the invitation if email sending fails
            invitation.delete()
            logger.debug(
                f"Invitation deleted due to email sending failure: {invitation.email}"
            )
            return redirect("shifts:staff_list")

        return super().form_valid(form)


class AcceptInvitationView(View):
    """Allows a user to accept an invitation to join as a staff member."""

    def get(self, request, token, *args, **kwargs):
        invitation = get_object_or_404(Invitation, token=token, is_active=True)
        form = AcceptInvitationForm(initial={"email": invitation.email})
        return render(request, "accounts/accept_invitation.html", {"form": form})

    def post(self, request, token, *args, **kwargs):
        invitation = get_object_or_404(Invitation, token=token, is_active=True)
        form = AcceptInvitationForm(request.POST, initial={"email": invitation.email}, invitation=invitation, request=request)
        if form.is_valid():
            # Create the user
            user = form.save()

            # Assign the user to the 'Agency Staff' group
            agency_staff_group, created = Group.objects.get_or_create(
                name="Agency Staff"
            )
            user.groups.add(agency_staff_group)
            logger.info(f"User {user.username} assigned to 'Agency Staff' group.")

            # Link the user to the agency associated with the invitation if applicable
            if invitation.agency:
                user.profile.agency = invitation.agency
                user.profile.save()
                logger.debug(
                    f"User {user.username} linked to agency {invitation.agency.name}."
                )
            else:
                logger.debug(f"User {user.username} not linked to any agency.")

            # Mark the invitation as used
            invitation.is_active = False
            invitation.accepted_at = timezone.now()
            invitation.save()
            logger.info(
                f"Invitation {invitation.email} marked as accepted by {user.username}."
            )

            # Log the user in
            login(request, user)
            messages.success(request, "Your account has been created successfully.")
            logger.info(f"User {user.username} logged in after accepting invitation.")
            return redirect("accounts:staff_dashboard")  # Redirect to staff dashboard
        else:
            messages.error(request, "Please correct the errors below.")
            logger.warning(f"Invalid acceptance form submitted by {invitation.email}")
            return render(request, "accounts/accept_invitation.html", {"form": form})


# ---------------------------
# Address Lookup FBV
# ---------------------------


@login_required
def get_address(request):
    """AJAX view to fetch address details from address_line1."""
    address_line1 = request.GET.get("address_line1")
    if not address_line1:
        return JsonResponse({"success": False, "message": "No address provided."})
    # Retrieve addresses using the utility function
    addresses = get_address_from_address_line1(address_line1)
    if addresses:
        return JsonResponse({"success": True, "addresses": addresses})
    else:
        return JsonResponse(
            {
                "success": False,
                "message": "No addresses found for the provided address.",
            }
        )


# ---------------------------
# Manage Agencies CBVs
# ---------------------------


class AgencyListView(
    LoginRequiredMixin, AgencyOwnerRequiredMixin, SubscriptionRequiredMixin, ListView
):
    """Allows superusers or agency owners to manage agencies."""

    model = Agency
    template_name = "accounts/manage_agencies.html"
    context_object_name = "agencies"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Agency.objects.all()
        else:
            return Agency.objects.filter(id=self.request.user.profile.agency.id)


class AgencyCreateView(
    LoginRequiredMixin, SuperuserRequiredMixin, SubscriptionRequiredMixin, CreateView
):
    """Allows superusers to create a new agency."""

    # Only superusers should create agencies; agency owners manage their own
    model = Agency
    form_class = AgencyForm
    template_name = "accounts/agency_form.html"
    success_url = reverse_lazy("accounts:manage_agencies")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Agency created successfully.")
        logger.info(
            f"Agency '{form.instance.name}' created by user {self.request.user.username}."
        )
        return response


class AgencyUpdateView(
    LoginRequiredMixin, AgencyOwnerRequiredMixin, SubscriptionRequiredMixin, UpdateView
):
    """Allows superusers or agency owners to edit their agency."""

    model = Agency
    form_class = AgencyForm
    template_name = "accounts/agency_form.html"
    success_url = reverse_lazy("accounts:manage_agencies")

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Agency.objects.all()
        else:
            return Agency.objects.filter(id=self.request.user.profile.agency.id)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Agency updated successfully.")
        logger.info(
            f"Agency '{form.instance.name}' updated by user {self.request.user.username}."
        )
        return response


class AgencyDeleteView(
    LoginRequiredMixin, SuperuserRequiredMixin, SubscriptionRequiredMixin, DeleteView
):
    """Allows superusers to delete an agency."""

    model = Agency
    template_name = "accounts/agency_confirm_delete.html"
    success_url = reverse_lazy("accounts:manage_agencies")

    def delete(self, request, *args, **kwargs):
        agency = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Agency deleted successfully.")
        logger.info(f"Agency '{agency.name}' deleted by user {request.user.username}.")
        return response


# ---------------------------
# Manage Users CBVs
# ---------------------------


class UserListView(
    LoginRequiredMixin, AgencyManagerRequiredMixin, SubscriptionRequiredMixin, ListView
):
    """Allows superusers or agency managers to manage users."""

    model = User
    template_name = "accounts/manage_users.html"
    context_object_name = "users"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(profile__agency=self.request.user.profile.agency)


class UserCreateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    CreateView,
):
    """Allows superusers or agency managers to create a new user."""

    model = User
    form_class = UserForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:manage_users")

    def form_valid(self, form):
        user = form.save()
        group = form.cleaned_data.get("group")
        if group:
            user.groups.add(group)
            logger.info(f"User '{user.username}' added to group '{group.name}'.")
        messages.success(self.request, "User created successfully.")
        logger.info(f"User '{user.username}' created by {self.request.user.username}.")
        return super().form_valid(form)


class UserUpdateView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    UpdateView,
):
    """Allows superusers or agency managers to edit an existing user."""

    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:manage_users")

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(profile__agency=self.request.user.profile.agency)

    def form_valid(self, form):
        user = form.save()
        group = form.cleaned_data.get("group")
        if group:
            user.groups.clear()
            user.groups.add(group)
            logger.info(
                f"User '{user.username}' updated and assigned to group '{group.name}'."
            )
        messages.success(self.request, "User updated successfully.")
        return super().form_valid(form)


class UserDeleteView(
    LoginRequiredMixin,
    AgencyManagerRequiredMixin,
    SubscriptionRequiredMixin,
    DeleteView,
):
    """Allows superusers or agency managers to delete a user."""

    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:manage_users")

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(profile__agency=self.request.user.profile.agency)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        messages.success(request, "User deactivated successfully.")
        logger.info(
            f"User '{user.username}' deactivated by user {request.user.username}."
        )
        return redirect(self.success_url)