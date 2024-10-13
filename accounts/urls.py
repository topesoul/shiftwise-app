from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='account_signup'),
    path('profile/', views.profile_view, name='account_profile'),
    path('login/', views.login_view, name='account_login'),
    path('logout/', views.logout_view, name='account_logout'),
]