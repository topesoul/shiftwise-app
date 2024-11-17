# /workspace/shiftwise/home/urls.py

from django.urls import path

from .views import HomeView

app_name = "home"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]
