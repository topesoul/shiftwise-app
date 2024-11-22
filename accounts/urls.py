# /workspace/shiftwise/accounts/urls.py

from django.urls import path

# Authentication and MFA Views
# ----------------------------
from .views import (
    CustomLoginView,
    LogoutView,
    MFAVerifyView,
    ActivateTOTPView,
    DisableTOTPView,
    ResendTOTPCodeView,
)

# Signup Views
# ------------
from .views import (
    SignUpView,
    SignupSelectionView,
    AgencySignUpView,
)

# Profile and Dashboard Views
# ---------------------------
from .views import (
    ProfileView,
    AgencyDashboardView,
    StaffDashboardView,
    SuperuserDashboardView,
)

# Invitation Views
# ----------------
from .views import (
    InviteStaffView,
    AcceptInvitationView,
)

# Address-related Function
# ------------------------
from .views import get_address

# Agency Management Views
# -----------------------
from .views import (
    AgencyListView,
    AgencyCreateView,
    AgencyUpdateView,
    AgencyDeleteView,
)

# User Management Views
# ---------------------
from .views import (
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
)

app_name = 'accounts'

urlpatterns = [
    # Authentication and MFA URLs
    # ---------------------------
    path('login/', CustomLoginView.as_view(), name='login_view'),
    path('logout/', LogoutView.as_view(), name='logout_view'),
    path('mfa-verify/', MFAVerifyView.as_view(), name='mfa_verify'),
    path('activate-totp/', ActivateTOTPView.as_view(), name='activate_totp'),
    path('disable-totp/', DisableTOTPView.as_view(), name='disable_totp'),
    path('resend-totp/', ResendTOTPCodeView.as_view(), name='resend_totp'),

    # Signup URLs
    # -----------
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signup-selection/', SignupSelectionView.as_view(), name='signup_selection'),
    path('agency-signup/', AgencySignUpView.as_view(), name='agency_signup'),

    # Profile and Dashboard URLs
    # --------------------------
    path('profile/', ProfileView.as_view(), name='profile'),
    path('agency-dashboard/', AgencyDashboardView.as_view(), name='agency_dashboard'),
    path('staff-dashboard/', StaffDashboardView.as_view(), name='staff_dashboard'),
    path('superuser-dashboard/', SuperuserDashboardView.as_view(), name='superuser_dashboard'),

    # Invitation URLs
    # ---------------
    path('invite-staff/', InviteStaffView.as_view(), name='invite_staff'),
    path('accept-invitation/<uuid:token>/', AcceptInvitationView.as_view(), name='accept_invitation'),

    # Address-related URL
    # -------------------
    path('get-address/', get_address, name='get_address'),

    # Agency Management URLs
    # ----------------------
    path('manage/agencies/', AgencyListView.as_view(), name='manage_agencies'),
    path('manage/agencies/create/', AgencyCreateView.as_view(), name='create_agency'),
    path('manage/agencies/<int:pk>/update/', AgencyUpdateView.as_view(), name='update_agency'),
    path('manage/agencies/<int:pk>/delete/', AgencyDeleteView.as_view(), name='delete_agency'),

    # User Management URLs
    # --------------------
    path('manage/users/', UserListView.as_view(), name='manage_users'),
    path('manage/users/create/', UserCreateView.as_view(), name='create_user'),
    path('manage/users/<int:pk>/update/', UserUpdateView.as_view(), name='update_user'),
    path('manage/users/<int:pk>/delete/', UserDeleteView.as_view(), name='delete_user'),
]