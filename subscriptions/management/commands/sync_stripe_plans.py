# /workspace/shiftwise/subscriptions/management/commands/sync_stripe_plans.py

from django.core.management.base import BaseCommand
from subscriptions.models import Plan
import stripe
from django.conf import settings
from decimal import Decimal


class Command(BaseCommand):
    help = "Sync subscription plans from Stripe to Django models"

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Retrieve all GBP prices from Stripe
            prices = stripe.Price.list(currency="gbp", expand=["data.product"])
            for price in prices.auto_paging_iter():
                product = price.product
                plan_name = product["name"]

                # Retrieve description from the Product; if missing, use plan_name as default
                description = product.get("description") or plan_name

                billing_cycle = price.recurring["interval"]

                # Determine display string based on billing cycle
                if billing_cycle == "month":
                    billing_cycle_display = "monthly"
                elif billing_cycle == "year":
                    billing_cycle_display = "yearly"
                else:
                    billing_cycle_display = "unknown"

                # Convert unit_amount_decimal from string to Decimal
                try:
                    price_amount = (
                        Decimal(price.unit_amount_decimal) / 100
                    )  # Convert from pence to pounds
                except (ValueError, TypeError):
                    self.stderr.write(
                        self.style.ERROR(
                            f"Invalid unit_amount_decimal for price ID {price.id}"
                        )
                    )
                    continue  # Skip this price

                # Find existing plan or create a new one
                plan, created = Plan.objects.get_or_create(
                    name=plan_name,
                    billing_cycle=billing_cycle_display,
                    defaults={
                        "description": description,
                        "stripe_price_id": price.id,
                        "features": {},  # Populate with actual features if available
                        "price": price_amount,
                    },
                )
                if not created:
                    # Update existing plan
                    plan.description = description
                    plan.stripe_price_id = price.id
                    plan.price = price_amount
                    # Update features as needed
                    plan.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Synced plan: {plan_name} ({billing_cycle_display})"
                    )
                )

        except stripe.error.StripeError as e:
            self.stderr.write(self.style.ERROR(f"Stripe Error: {str(e)}"))
