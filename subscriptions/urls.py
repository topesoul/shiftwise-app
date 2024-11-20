# /workspace/shiftwise/subscriptions/urls.py

from django.urls import path
from .views import (
    SubscriptionHomeView,
    SubscribeView,
    subscription_success,
    subscription_cancel,
    StripeWebhookView,
    UpgradeSubscriptionView,
    DowngradeSubscriptionView,
    CancelSubscriptionView,
    ManageSubscriptionView,
    UpdatePaymentMethodView,
)

app_name = 'subscriptions'

urlpatterns = [
    path('', SubscriptionHomeView.as_view(), name='subscription_home'),
    path('subscribe/<int:plan_id>/', SubscribeView.as_view(), name='subscribe'),
    path('success/', subscription_success, name='subscription_success'),
    path('cancelled/', subscription_cancel, name='subscription_cancel'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('upgrade/<int:plan_id>/', UpgradeSubscriptionView.as_view(), name='upgrade_subscription'),
    path('downgrade/<int:plan_id>/', DowngradeSubscriptionView.as_view(), name='downgrade_subscription'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('manage/', ManageSubscriptionView.as_view(), name='manage_subscription'),
    path('update_payment_method/', UpdatePaymentMethodView.as_view(), name='update_payment_method'),
]
