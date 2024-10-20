# shifts/mixins.py

from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from billing.models import Subscription


class AgencyManagerRequiredMixin(AccessMixin):
    """
    Verify that the current user is an agency manager or a superuser.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.groups.filter(name='Agency Managers').exists()):
            raise PermissionDenied("You must be an Agency Manager to access this page.")
        return super().dispatch(request, *args, **kwargs)


class AgencyStaffRequiredMixin(AccessMixin):
    """
    Verify that the current user is an agency staff member.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.groups.filter(name='Agency Staff').exists():
            raise PermissionDenied("You must be an Agency Staff member to access this page.")
        return super().dispatch(request, *args, **kwargs)


class SubscriptionRequiredMixin(UserPassesTestMixin):
    """
    Verify that the current user has an active subscription.
    Redirects to the subscription page with an error message if not.
    """

    def test_func(self):
        subscription = getattr(self.request.user, 'subscription', None)
        return subscription and subscription.active

    def handle_no_permission(self):
        messages.error(self.request, "You need an active subscription to access this feature.")
        return redirect('billing:subscribe')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)