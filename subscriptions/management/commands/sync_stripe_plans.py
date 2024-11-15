# /workspace/shiftwise/subscriptions/management/commands/sync_stripe_plans.py

from django.core.management.base import BaseCommand
from subscriptions.models import Plan
import stripe
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sync subscription plans from Stripe to Django models"

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Retrieve all active GBP prices from Stripe
            prices = stripe.Price.list(currency="gbp", active=True, expand=["data.product"])

            # Collect all Stripe price IDs to identify inactive plans later
            synced_stripe_price_ids = []

            for price in prices.auto_paging_iter():
                product = price.product
                original_plan_name = product["name"]

                # Map Stripe product names to valid plan names
                if original_plan_name.startswith("Basic"):
                    plan_name = "Basic"
                elif original_plan_name.startswith("Pro"):
                    plan_name = "Pro"
                elif original_plan_name.startswith("Enterprise"):
                    plan_name = "Enterprise"
                else:
                    self.stderr.write(
                        self.style.ERROR(
                            f"Unknown product name '{original_plan_name}' for price ID {price.id}. Skipping."
                        )
                    )
                    logger.error(
                        f"Unknown product name '{original_plan_name}' for price ID {price.id}. Skipping."
                    )
                    continue  # Skip unknown plan names

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
                    price_amount = Decimal(price.unit_amount_decimal) / 100  # Convert from pence to pounds
                except (ValueError, TypeError):
                    self.stderr.write(
                        self.style.ERROR(
                            f"Invalid unit_amount_decimal for price ID {price.id}"
                        )
                    )
                    logger.error(
                        f"Invalid unit_amount_decimal for price ID {price.id}"
                    )
                    continue  # Skip this price

                # Map Stripe product metadata to feature flags
                metadata = product.get("metadata", {})
                notifications_enabled = metadata.get("notifications_enabled", "false").lower() == "true"
                advanced_reporting = metadata.get("advanced_reporting", "false").lower() == "true"
                priority_support = metadata.get("priority_support", "false").lower() == "true"
                shift_management = metadata.get("shift_management", "false").lower() == "true"
                staff_performance = metadata.get("staff_performance", "false").lower() == "true"
                custom_integrations = metadata.get("custom_integrations", "false").lower() == "true"

                # Find existing plan or create a new one based on stripe_price_id
                plan, created = Plan.objects.get_or_create(
                    stripe_price_id=price.id,
                    defaults={
                        "name": plan_name,
                        "billing_cycle": billing_cycle_display,
                        "description": description,
                        "stripe_product_id": product.id,
                        "price": price_amount,
                        "notifications_enabled": notifications_enabled,
                        "advanced_reporting": advanced_reporting,
                        "priority_support": priority_support,
                        "shift_management": shift_management,
                        "staff_performance": staff_performance,
                        "custom_integrations": custom_integrations,
                        "is_active": True,
                    },
                )

                synced_stripe_price_ids.append(price.id)

                if not created:
                    # Update existing plan
                    plan.billing_cycle = billing_cycle_display
                    plan.description = description
                    plan.stripe_product_id = product.id
                    plan.price = price_amount
                    plan.notifications_enabled = notifications_enabled
                    plan.advanced_reporting = advanced_reporting
                    plan.priority_support = priority_support
                    plan.shift_management = shift_management
                    plan.staff_performance = staff_performance
                    plan.custom_integrations = custom_integrations
                    plan.is_active = True
                    plan.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated plan: {plan_name} ({billing_cycle_display})"
                        )
                    )
                    logger.info(
                        f"Updated plan: {plan_name} ({billing_cycle_display}) from Stripe price ID {price.id}"
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created plan: {plan_name} ({billing_cycle_display})"
                        )
                    )
                    logger.info(
                        f"Created plan: {plan_name} ({billing_cycle_display}) with Stripe price ID {price.id}"
                    )

            # Deactivate plans that are no longer active in Stripe
            existing_active_plans = Plan.objects.filter(is_active=True)
            for plan in existing_active_plans:
                if plan.stripe_price_id not in synced_stripe_price_ids:
                    plan.is_active = False
                    plan.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f"Deactivated plan: {plan.name} ({plan.billing_cycle}) as it's no longer active in Stripe."
                        )
                    )
                    logger.info(
                        f"Deactivated plan: {plan.name} ({plan.billing_cycle}) as it's no longer active in Stripe."
                    )

        except stripe.error.StripeError as e:
            self.stderr.write(self.style.ERROR(f"Stripe Error: {str(e)}"))
            logger.error(f"Stripe Error during sync_stripe_plans: {str(e)}")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected Error: {str(e)}"))
            logger.exception(f"Unexpected Error during sync_stripe_plans: {str(e)}")
