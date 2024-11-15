# /workspace/shiftwise/subscriptions/services.py

from subscriptions.models import Subscription
from shifts.models import Shift
from django.utils import timezone

class SubscriptionLimitChecker:
    @staticmethod
    def check_shift_limit(agency):
        """
        Checks if the agency has reached its shift limit based on the current subscription plan.
        Returns True if within limits, False otherwise.
        """
        try:
            subscription = Subscription.objects.get(agency=agency, is_active=True, current_period_end__gt=timezone.now())
            plan = subscription.plan
            if not plan:
                return False

            shift_count = Shift.objects.filter(agency=agency, created_at__gte=timezone.now().replace(day=1)).count()
            if plan.shift_management and shift_count >= getattr(plan, 'shift_limit', 0):
                return False
            return True
        except Subscription.DoesNotExist:
            return False