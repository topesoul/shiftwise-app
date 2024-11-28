# /workspace/shiftwise/core/urls.py
from django.urls import path

from .views import google_maps_proxy

app_name = "core"

urlpatterns = [
    path("proxy/google-maps-api.js", google_maps_proxy, name="google_maps_proxy"),
]
