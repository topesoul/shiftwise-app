# /workspace/shiftwise/shiftwise/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("shifts/", include("shifts.urls", namespace="shifts")),
    path(
        "accounts/", include(("accounts.urls", "accounts"), namespace="accounts")
    ),  # Custom accounts
    path("auth/", include("allauth.urls")),  # Allauth under 'auth/'
    path("contact/", include("contact.urls", namespace="contact")),
    path("subscriptions/", include("subscriptions.urls", namespace="subscriptions")),
    path("", include("home.urls", namespace="home")),
]

handler403 = "shifts.views.custom_permission_denied_view"
handler404 = "shifts.views.custom_page_not_found_view"
handler500 = "shifts.views.custom_server_error_view"

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
