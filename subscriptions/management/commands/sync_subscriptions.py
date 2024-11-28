# /workspace/shiftwise/subscriptions/management/commands/sync_subscriptions.py

from datetime import datetime, timezone

import stripe
from django.conf import settings
from django.core.management.base import BaseCommand

from accounts.models import Agency
from subscriptions.models import Plan, Subscription


class Command(BaseCommand):
    help = "Synchronize local subscriptions with Stripe"

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        subscriptions = stripe.Subscription.list(limit=100)

        for stripe_sub in subscriptions.auto_paging_iter():
            try:
                # Get the agency based on stripe_customer_id
                agency = Agency.objects.get(stripe_customer_id=stripe_sub.customer)
            except Agency.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Agency with customer ID {stripe_sub.customer} does not exist."
                    )
                )
                continue  # Skip to the next subscription

            # Proceed if agency exists
            try:
                plan_id = stripe_sub["items"]["data"][0]["price"]["id"]
                plan = Plan.objects.get(stripe_price_id=plan_id)

                current_period_start = datetime.fromtimestamp(
                    stripe_sub.current_period_start, tz=timezone.utc
                )
                current_period_end = datetime.fromtimestamp(
                    stripe_sub.current_period_end, tz=timezone.utc
                )

                # Use 'agency' as the unique identifier for get_or_create
                subscription, created = Subscription.objects.get_or_create(
                    agency=agency,
                    defaults={
                        "stripe_subscription_id": stripe_sub.id,
                        "plan": plan,
                        "is_active": stripe_sub.status == "active",
                        "status": stripe_sub.status,
                        "current_period_start": current_period_start,
                        "current_period_end": current_period_end,
                        "is_expired": stripe_sub.status in ["canceled", "unpaid"],
                    },
                )

                if not created:
                    # Update existing subscription
                    subscription.stripe_subscription_id = stripe_sub.id
                    subscription.plan = plan
                    subscription.is_active = stripe_sub.status == "active"
                    subscription.status = stripe_sub.status
                    subscription.current_period_start = current_period_start
                    subscription.current_period_end = current_period_end
                    subscription.is_expired = stripe_sub.status in [
                        "canceled",
                        "unpaid",
                    ]
                    subscription.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processed subscription {stripe_sub.id} for agency {agency.name}"
                    )
                )

            except Plan.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Plan with price ID {plan_id} does not exist.")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing subscription {stripe_sub.id}: {e}"
                    )
                )
