# /workspace/shiftwise/core/urls.py
from django.urls import path

from .views import google_maps_proxy, serve_well_known_file

app_name = "core"

urlpatterns = [
    path("proxy/google-maps-api.js", google_maps_proxy, name="google_maps_proxy"),
    path(".well-known/pki-validation/<str:filename>",serve_well_known_file, name="serve_well_known_file",
    ),
]