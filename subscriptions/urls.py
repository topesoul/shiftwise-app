# /workspace/shiftwise/subscriptions/urls.py

from django.urls import path
from .views import (
    SubscriptionHomeView,
    SubscribeView,
    ManageSubscriptionView,
    CancelSubscriptionView,
    UpdatePaymentMethodView,
    UpgradeSubscriptionView,
    DowngradeSubscriptionView,
    subscription_success,
    subscription_cancel,
    stripe_webhook,
)

app_name = 'subscriptions'

urlpatterns = [
    path('', SubscriptionHomeView.as_view(), name='subscription_home'),
    path('subscribe/<int:plan_id>/', SubscribeView.as_view(), name='subscribe'),
    path('manage/', ManageSubscriptionView.as_view(), name='manage_subscription'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('update-payment/', UpdatePaymentMethodView.as_view(), name='update_payment_method'),
    path('upgrade/', UpgradeSubscriptionView.as_view(), name='upgrade_subscription'),
    path('downgrade/', DowngradeSubscriptionView.as_view(), name='downgrade_subscription'),
    path('success/', subscription_success, name='subscription_success'),
    path('cancelled/', subscription_cancel, name='subscription_cancel'),
    path('webhook/', stripe_webhook, name='stripe_webhook'),
]
