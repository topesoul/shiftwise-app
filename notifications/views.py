# notifications/views.py

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, View

from core.mixins import FeatureRequiredMixin, SubscriptionRequiredMixin

from .models import Notification

logger = logging.getLogger(__name__)


class NotificationListView(
    LoginRequiredMixin, FeatureRequiredMixin, SubscriptionRequiredMixin, ListView
):
    """
    Displays a list of notifications for the user.
    """

    required_features = ["notifications_enabled"]
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


class MarkNotificationReadView(LoginRequiredMixin, FeatureRequiredMixin, View):
    """
    Marks a notification as read via AJAX.
    """

    required_features = ["notifications_enabled"]

    @method_decorator(csrf_protect)
    def post(self, request, notification_id, *args, **kwargs):
        notification = get_object_or_404(
            Notification, id=notification_id, user=request.user
        )
        notification.read = True
        notification.save()
        logger.info(
            f"Notification ID {notification.id} marked as read by {request.user.username}."
        )
        return JsonResponse({"success": True})
