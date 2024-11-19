# /workspace/shiftwise/subscriptions/urls.py

from django.urls import path

from .views import (
    CancelSubscriptionView,
    DowngradeSubscriptionView,
    ManageSubscriptionView,
    SubscribeView,
    SubscriptionHomeView,
    UpdatePaymentMethodView,
    UpgradeSubscriptionView,
    StripeWebhookView,
    subscription_cancel,
    subscription_success,
)

app_name = "subscriptions"

urlpatterns = [
    # Subscription Home
    path("", SubscriptionHomeView.as_view(), name="subscription_home"),

    # Subscribe to a Plan
    path("subscribe/<int:plan_id>/", SubscribeView.as_view(), name="subscribe"),

    # Manage Subscription
    path("manage/", ManageSubscriptionView.as_view(), name="manage_subscription"),

    # Cancel Subscription
    path("cancel/", CancelSubscriptionView.as_view(), name="cancel_subscription"),

    # Update Payment Method
    path(
        "update-payment/",
        UpdatePaymentMethodView.as_view(),
        name="update_payment_method",
    ),

    # Upgrade Subscription
    path("upgrade/", UpgradeSubscriptionView.as_view(), name="upgrade_subscription"),

    # Downgrade Subscription
    path(
        "downgrade/", DowngradeSubscriptionView.as_view(), name="downgrade_subscription"
    ),

    # Subscription Success and Cancellation Pages
    path("success/", subscription_success, name="subscription_success"),
    path("cancelled/", subscription_cancel, name="subscription_cancel"),

    # Stripe Webhook
    path("webhook/", StripeWebhookView.as_view(), name="stripe_webhook"),
]