# /workspace/shiftwise/subscriptions/urls.py

from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.SubscriptionHomeView.as_view(), name="subscription_home"),
    path("subscribe/<int:plan_id>/", views.SubscribeView.as_view(), name="subscribe"),
    path("success/", views.subscription_success, name="subscription_success"),
    path("cancel/", views.subscription_cancel, name="subscription_cancel"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
    path("upgrade/", views.UpgradeSubscriptionView.as_view(), name="upgrade_subscription"),
    path("downgrade/", views.DowngradeSubscriptionView.as_view(), name="downgrade_subscription"),
]
