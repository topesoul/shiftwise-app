# /workspace/shiftwise/accounts/urls.py

from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.LoginView.as_view(), name="login_view"),
    path("logout/", views.LogoutView.as_view(), name="logout_view"),
    path(
        "signup_selection/",
        views.SignupSelectionView.as_view(),
        name="signup_selection",
    ),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("agency_signup/", views.AgencySignUpView.as_view(), name="agency_signup"),
    path("mfa/activate/", views.ActivateTOTPView.as_view(), name="activate_totp"),
    path("mfa/verify/", views.VerifyTOTPView.as_view(), name="verify_totp"),
    path("mfa/disable/", views.DisableTOTPView.as_view(), name="disable_totp"),
    path(
        "mfa/resend_code/", views.ResendTOTPCodeView.as_view(), name="resend_totp_code"
    ),
    path(
        "mfa/authenticate/",
        views.VerifyTOTPView.as_view(),
        name="account_mfa_authenticate",
    ),
    # Profile
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Dashboards
    path(
        "agency_dashboard/",
        views.AgencyDashboardView.as_view(),
        name="agency_dashboard",
    ),
    path(
        "staff_dashboard/", views.StaffDashboardView.as_view(), name="staff_dashboard"
    ),
    path(
        "superuser_dashboard/",
        views.SuperuserDashboardView.as_view(),
        name="superuser_dashboard",
    ),
    # Invitations
    path("invite_staff/", views.InviteStaffView.as_view(), name="invite_staff"),
    path(
        "accept_invitation/<uuid:token>/",
        views.AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
    # Address Lookup
    path("get_address/", views.get_address, name="get_address"),  # Function-Based View
    # Manage Agencies
    path("manage_agencies/", views.AgencyListView.as_view(), name="manage_agencies"),
    path(
        "manage_agencies/create/",
        views.AgencyCreateView.as_view(),
        name="manage_agencies_create",
    ),
    path(
        "manage_agencies/edit/<int:pk>/",
        views.AgencyUpdateView.as_view(),
        name="manage_agencies_edit",
    ),
    path(
        "manage_agencies/delete/<int:pk>/",
        views.AgencyDeleteView.as_view(),
        name="manage_agencies_delete",
    ),
    # Manage Users
    path("manage_users/", views.UserListView.as_view(), name="manage_users"),
    path(
        "manage_users/create/",
        views.UserCreateView.as_view(),
        name="manage_users_create",
    ),
    path(
        "manage_users/edit/<int:pk>/",
        views.UserUpdateView.as_view(),
        name="manage_users_edit",
    ),
    path(
        "manage_users/delete/<int:pk>/",
        views.UserDeleteView.as_view(),
        name="manage_users_delete",
    ),
]
