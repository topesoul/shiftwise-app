# /workspace/shiftwise/subscriptions/services.py

from django.utils import timezone

from shifts.models import Shift
from subscriptions.models import Subscription


class SubscriptionLimitChecker:
    @staticmethod
    def check_shift_limit(agency):
        """
        Checks if the agency has reached its shift limit based on the current subscription plan.
        Returns True if within limits, False otherwise.
        """
        try:
            subscription = Subscription.objects.get(
                agency=agency, is_active=True, current_period_end__gt=timezone.now()
            )
            plan = subscription.plan
            if not plan:
                return False

            # Get the first day of the current month
            first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            shift_count = Shift.objects.filter(
                agency=agency, created_at__gte=first_day_of_month
            ).count()
            if plan.shift_management:
                if plan.shift_limit:
                    if shift_count >= plan.shift_limit:
                        return False
            return True
        except Subscription.DoesNotExist:
            return False