# /workspace/shiftwise/accounts/urls.py

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication URLs
    path("login/", views.LoginView.as_view(), name="login_view"),
    path("logout/", views.LogoutView.as_view(), name="logout_view"),
    path("signup/", views.SignupSelectionView.as_view(), name="signup_selection"),
    path("signup/agency/", views.AgencySignUpView.as_view(), name="agency_signup"),
    path(
        "signup/invitation/<str:token>/",
        views.AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
    # Dashboard URLs
    path(
        "dashboard/superuser/",
        views.SuperuserDashboardView.as_view(),
        name="superuser_dashboard",
    ),
    path(
        "dashboard/agency/",
        views.AgencyDashboardView.as_view(),
        name="agency_dashboard",
    ),
    path(
        "dashboard/staff/", views.StaffDashboardView.as_view(), name="staff_dashboard"
    ),
    # Profile URL
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # MFA URLs
    path("mfa/activate/", views.ActivateTOTPView.as_view(), name="activate_totp"),
    path("mfa/verify/", views.VerifyTOTPView.as_view(), name="verify_totp"),
    path("mfa/disable/", views.DisableTOTPView.as_view(), name="disable_totp"),
    path("mfa/resend/", views.ResendTOTPCodeView.as_view(), name="resend_totp"),
    # Agency Management URLs
    path("agencies/", views.AgencyListView.as_view(), name="manage_agencies"),
    path(
        "agencies/create/", views.AgencyCreateView.as_view(), name="agency_create"
    ),  # Ensure correct name
    path(
        "agencies/update/<int:pk>/",
        views.AgencyUpdateView.as_view(),
        name="manage_agencies_edit",
    ),
    path(
        "agencies/delete/<int:pk>/",
        views.AgencyDeleteView.as_view(),
        name="manage_agencies_delete",
    ),
    # User Management URLs
    path("users/", views.UserListView.as_view(), name="manage_users"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path(
        "users/update/<int:pk>/",
        views.UserUpdateView.as_view(),
        name="manage_users_edit",
    ),
    path(
        "users/delete/<int:pk>/",
        views.UserDeleteView.as_view(),
        name="manage_users_delete",
    ),
    # Invitation URLs
    path("invite_staff/", views.InviteStaffView.as_view(), name="invite_staff"),
]
