# /workspace/shiftwise/accounts/urls.py

from django.urls import path
from .views import (
    CustomLoginView,
    LogoutView,
    MFAVerifyView,
    SignUpView,
    SignupSelectionView,
    AgencySignUpView,
    ActivateTOTPView,
    DisableTOTPView,
    ResendTOTPCodeView,
    ProfileView,
    AgencyDashboardView,
    StaffDashboardView,
    SuperuserDashboardView,
    InviteStaffView,
    AcceptInvitationView,
    get_address,
    AgencyListView,
    AgencyCreateView,
    AgencyUpdateView,
    AgencyDeleteView,
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login_view'),
    path('logout/', LogoutView.as_view(), name='logout_view'),
    path('mfa_verify/', MFAVerifyView.as_view(), name='mfa_verify'),
    path('signup/', SignUpView.as_view(), name='signup_view'),
    path('signup_selection/', SignupSelectionView.as_view(), name='signup_selection'),
    path('agency_signup/', AgencySignUpView.as_view(), name='agency_signup'),
    path('activate_totp/', ActivateTOTPView.as_view(), name='activate_totp'),
    path('deactivate_totp/', DisableTOTPView.as_view(), name='deactivate_totp'),
    path('reauthenticate/', ResendTOTPCodeView.as_view(), name='reauthenticate'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('superuser_dashboard/', SuperuserDashboardView.as_view(), name='superuser_dashboard'),
    path('agency_dashboard/', AgencyDashboardView.as_view(), name='agency_dashboard'),
    path('staff_dashboard/', StaffDashboardView.as_view(), name='staff_dashboard'),
    path('invite_staff/', InviteStaffView.as_view(), name='invite_staff'),
    path('accept_invitation/<str:token>/', AcceptInvitationView.as_view(), name='accept_invitation'),
    path('address_lookup/', get_address, name='address_lookup'),

    # Agency management URLs
    path('manage_agencies/', AgencyListView.as_view(), name='manage_agencies'),
    path('create_agency/', AgencyCreateView.as_view(), name='create_agency'),
    path('update_agency/<int:pk>/', AgencyUpdateView.as_view(), name='update_agency'),
    path('delete_agency/<int:pk>/', AgencyDeleteView.as_view(), name='delete_agency'),

    # User management URLs
    path('manage_users/', UserListView.as_view(), name='manage_users'),
    path('create_user/', UserCreateView.as_view(), name='create_user'),
    path('update_user/<int:pk>/', UserUpdateView.as_view(), name='update_user'),
    path('delete_user/<int:pk>/', UserDeleteView.as_view(), name='delete_user'),
]
