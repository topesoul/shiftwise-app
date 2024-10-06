from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('signup/', views.custom_signup, name='signup'),
    path('profile/', views.profile, name='profile'),
]
