# /workspace/shiftwise/subscriptions/views.py

import logging
from collections import defaultdict
from datetime import datetime, timezone as datetime_timezone

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.db.models import Q

from accounts.models import Agency, Profile
from core.mixins import AgencyOwnerRequiredMixin
from subscriptions.models import Plan, Subscription

from .utils import create_stripe_customer

# Initialize logger
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionHomeView(LoginRequiredMixin, TemplateView):
    template_name = "subscriptions/subscription_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                messages.error(
                    self.request, "User profile does not exist. Please contact support."
                )
                logger.error(f"Profile does not exist for user: {user.username}")
                return context

            agency = profile.agency

            if agency is None:
                messages.error(
                    self.request,
                    "Your agency information is missing. Please contact support.",
                )
                logger.error(f"Agency is None for user: {user.username}")
                return context

            # Get current subscription
            try:
                subscription = agency.subscription
                if (
                    subscription.is_active
                    and subscription.current_period_end
                    and subscription.current_period_end > timezone.now()
                ):
                    context["subscription"] = subscription
                    context["current_plan"] = subscription.plan
                    context["has_active_subscription"] = True
                else:
                    context["subscription"] = None
                    context["current_plan"] = None
                    context["has_active_subscription"] = False
            except Subscription.DoesNotExist:
                context["subscription"] = None
                context["current_plan"] = None
                context["has_active_subscription"] = False
                logger.warning(f"No active subscription for agency: {agency.name}")
            except Exception as e:
                messages.error(
                    self.request,
                    "An error occurred while retrieving your subscription.",
                )
                logger.exception(f"Error retrieving subscription: {e}")
                context["subscription"] = None
                context["current_plan"] = None
                context["has_active_subscription"] = False

            # Retrieve all active plans
            plans = Plan.objects.filter(is_active=True).order_by(
                "name", "billing_cycle"
            )

            # Group plans by name and billing cycle
            plan_dict = defaultdict(dict)
            for plan in plans:
                if plan.billing_cycle.lower() == "monthly":
                    plan_dict[plan.name]["monthly_plan"] = plan
                elif plan.billing_cycle.lower() == "yearly":
                    plan_dict[plan.name]["yearly_plan"] = plan

            # Structure available_plans as a list of dictionaries
            available_plans = []
            for plan_name, plans in plan_dict.items():
                if not plans.get("monthly_plan") and not plans.get("yearly_plan"):
                    logger.warning(
                        f"No monthly or yearly plan found for {plan_name}. Skipping."
                    )
                    continue

                description = (
                    plans.get("monthly_plan").description
                    if plans.get("monthly_plan")
                    else plans.get("yearly_plan").description
                )

                available_plans.append(
                    {
                        "name": plan_name,
                        "description": description,
                        "monthly_plan": plans.get("monthly_plan"),
                        "yearly_plan": plans.get("yearly_plan"),
                    }
                )

            context["available_plans"] = available_plans

        return context


class SubscribeView(LoginRequiredMixin, View):
    def get(self, request, plan_id, *args, **kwargs):
        return self.process_subscription(request, plan_id)

    def post(self, request, plan_id, *args, **kwargs):
        return self.process_subscription(request, plan_id)

    def process_subscription(self, request, plan_id):
        user = request.user

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(request, "Please complete your profile before subscribing.")
            logger.error(f"Profile does not exist for user: {user.username}")
            return redirect("accounts:update_profile")

        agency = profile.agency
        if not agency:
            messages.error(request, "Please create an agency before subscribing.")
            logger.error(f"Agency is None for user: {user.username}")
            return redirect("accounts:create_agency")

        if not user.groups.filter(name="Agency Owners").exists():
            messages.error(request, "Only agency owners can subscribe.")
            logger.warning(
                f"User {user.username} attempted to subscribe without being an agency owner."
            )
            return redirect("subscriptions:subscription_home")

        plan = get_object_or_404(Plan, id=plan_id, is_active=True)

        if not agency.stripe_customer_id:
            messages.error(
                request, "Stripe customer ID is missing. Please contact support."
            )
            logger.error(f"Stripe customer ID is missing for agency: {agency.name}")
            return redirect("subscriptions:subscription_home")

        try:
            customer = stripe.Customer.retrieve(agency.stripe_customer_id)
            logger.info(
                f"Stripe customer retrieved for agency: {agency.name}, Customer ID: {customer.id}"
            )
        except stripe.error.StripeError as e:
            messages.error(request, "Failed to retrieve Stripe customer.")
            logger.exception(f"Stripe error while retrieving customer: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.exception(f"Unexpected error while retrieving customer: {e}")
            return redirect("subscriptions:subscription_home")

        if hasattr(agency, "subscription") and agency.subscription.is_active:
            messages.info(
                request,
                "You already have an active subscription. Manage your subscription instead.",
            )
            logger.info(f"Agency {agency.name} already has an active subscription.")
            return redirect("subscriptions:manage_subscription")

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": plan.stripe_price_id,
                        "quantity": 1,
                    },
                ],
                mode="subscription",
                success_url=request.build_absolute_uri(
                    reverse("subscriptions:subscription_success")
                ),
                cancel_url=request.build_absolute_uri(
                    reverse("subscriptions:subscription_cancel")
                ),
            )
            logger.info(
                f"Stripe Checkout Session created: {checkout_session.id} for agency: {agency.name}"
            )
            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            messages.error(request, "There was an error creating the checkout session.")
            logger.exception(f"Stripe error while creating checkout session: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.exception(f"Unexpected error while creating checkout session: {e}")
            return redirect("subscriptions:subscription_home")


def subscription_success(request):
    messages.success(request, "Your subscription was successful!")
    return render(request, "subscriptions/success.html")


def subscription_cancel(request):
    messages.error(request, "Your subscription was cancelled.")
    return render(request, "subscriptions/cancel.html")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        if not sig_header:
            logger.error("Missing Stripe signature header.")
            return HttpResponse(status=400)

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            logger.info(f"Stripe webhook received: {event['type']}")
        except ValueError as e:
            logger.exception(f"Invalid payload: {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.exception(f"Invalid signature: {e}")
            return HttpResponse(status=400)

        # Handle the event
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            self.handle_checkout_session_completed(event_data)
        elif event_type == "invoice.payment_succeeded":
            self.handle_invoice_paid(event_data)
        elif event_type == "customer.subscription.deleted":
            self.handle_subscription_deleted(event_data)
        elif event_type == "customer.subscription.updated":
            self.handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.created":
            self.handle_subscription_created(event_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")

        return HttpResponse(status=200)

    def handle_invoice_paid(self, invoice):
        """
        Handle the invoice.payment_succeeded event.
        This can be used to confirm the payment and update any related records.
        """
        stripe_subscription_id = invoice.get("subscription")
        if not stripe_subscription_id:
            logger.warning("Invoice does not contain a subscription ID.")
            return

        try:
            local_subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            logger.info(f"Invoice paid for subscription {stripe_subscription_id}.")

            # Ensure 'last_payment_date' exists in the Subscription model
            if hasattr(local_subscription, "last_payment_date"):
                local_subscription.last_payment_date = timezone.now()
                local_subscription.save()
                logger.info(
                    f"Updated last_payment_date for subscription {stripe_subscription_id}."
                )
            else:
                logger.warning(
                    f"'last_payment_date' field not found in Subscription model for {stripe_subscription_id}."
                )

        except Subscription.DoesNotExist:
            logger.error(
                f"No local subscription found for Stripe Subscription ID: {stripe_subscription_id}"
            )
        except Exception as e:
            logger.exception(f"Error handling invoice.payment_succeeded: {e}")

    def handle_subscription_deleted(self, subscription):
        stripe_subscription_id = subscription.get("id")
        logger.debug(
            f"Handling subscription deletion for Stripe Subscription ID: {stripe_subscription_id}"
        )
        try:
            local_subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            local_subscription.is_active = False
            local_subscription.status = "canceled"
            local_subscription.save()
            logger.info(f"Subscription {stripe_subscription_id} deactivated.")
        except Subscription.DoesNotExist:
            logger.warning(
                f"Subscription with ID {stripe_subscription_id} does not exist in the local database."
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error while handling subscription deletion: {e}"
            )

    def handle_subscription_updated(self, subscription):
        stripe_subscription_id = subscription.get("id")
        try:
            local_subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            local_subscription.is_active = subscription.get("status") == "active"
            local_subscription.status = subscription.get(
                "status", local_subscription.status
            )
            current_period_end = subscription.get("current_period_end")
            if current_period_end:
                local_subscription.current_period_end = datetime.fromtimestamp(
                    current_period_end, tz=datetime_timezone.utc
                )
            new_plan_id = subscription["items"]["data"][0]["price"]["id"]
            new_plan = Plan.objects.get(stripe_price_id=new_plan_id)
            local_subscription.plan = new_plan
            local_subscription.save()
            logger.info(
                f"Subscription updated to {new_plan.name} for agency: {local_subscription.agency.name}"
            )
        except Subscription.DoesNotExist:
            logger.error(
                f"Subscription with ID {stripe_subscription_id} does not exist in local database."
            )
            # Optional: Notify admin or create the subscription
        except Plan.DoesNotExist:
            logger.exception(
                f"Plan with price ID {subscription['items']['data'][0]['price']['id']} does not exist."
            )
        except ValidationError as ve:
            logger.exception(f"Validation error while updating subscription: {ve}")
        except Exception as e:
            logger.exception(
                f"Unexpected error while handling subscription update: {e}"
            )

    def handle_checkout_session_completed(self, session):
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        logger.debug(
            f"Processing checkout.session.completed for customer {customer_id}"
        )

        try:
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            logger.debug(f"Retrieved Stripe Subscription: {stripe_subscription}")

            plan_id = stripe_subscription["items"]["data"][0]["price"]["id"]
            logger.debug(f"Plan ID from Stripe: {plan_id}")

            current_period_start = datetime.fromtimestamp(
                stripe_subscription["current_period_start"], tz=datetime_timezone.utc
            )
            current_period_end = datetime.fromtimestamp(
                stripe_subscription["current_period_end"], tz=datetime_timezone.utc
            )

            agency = Agency.objects.get(stripe_customer_id=customer_id)
            logger.debug(f"Found Agency: {agency.name}")

            plan = Plan.objects.get(stripe_price_id=plan_id)
            logger.debug(f"Found Plan: {plan.name}")

            try:
                subscription = agency.subscription
                logger.debug(f"Existing Subscription found: {subscription}")
                subscription.plan = plan
                subscription.stripe_subscription_id = subscription_id
                subscription.is_active = True
                subscription.status = stripe_subscription["status"]
                subscription.current_period_start = current_period_start
                subscription.current_period_end = current_period_end
                subscription.is_expired = False
            except Subscription.DoesNotExist:
                logger.debug("No existing Subscription found. Creating a new one.")
                subscription = Subscription(
                    agency=agency,
                    plan=plan,
                    stripe_subscription_id=subscription_id,
                    is_active=True,
                    status=stripe_subscription["status"],
                    current_period_start=current_period_start,
                    current_period_end=current_period_end,
                    is_expired=False,
                )

            subscription.full_clean()
            subscription.save()
            logger.info(f"Subscription updated for agency {agency.name}")

        except Agency.DoesNotExist:
            logger.exception(f"Agency with customer ID {customer_id} does not exist.")
            return HttpResponse(status=400)
        except Plan.DoesNotExist:
            logger.exception(f"Plan with price ID {plan_id} does not exist.")
            return HttpResponse(status=400)
        except ValidationError as ve:
            logger.exception(f"Validation error while updating subscription: {ve}")
            return HttpResponse(status=400)
        except Exception as e:
            logger.exception(f"Unexpected error while handling checkout session: {e}")
            return HttpResponse(status=400)

    def handle_subscription_created(self, subscription):
        stripe_subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        plan_id = subscription["items"]["data"][0]["price"]["id"]
        current_period_start = datetime.fromtimestamp(
            subscription["current_period_start"], tz=datetime_timezone.utc
        )
        current_period_end = datetime.fromtimestamp(
            subscription["current_period_end"], tz=datetime_timezone.utc
        )

        logger.info(f"Subscription created: {stripe_subscription_id}")

        try:
            agency = Agency.objects.get(stripe_customer_id=customer_id)
            logger.debug(f"Found Agency: {agency.name}")

            plan = Plan.objects.get(stripe_price_id=plan_id)
            logger.debug(f"Found Plan: {plan.name}")

            subscription_record, created = Subscription.objects.get_or_create(
                stripe_subscription_id=stripe_subscription_id,
                agency=agency,
                defaults={
                    "plan": plan,
                    "is_active": True,
                    "status": subscription.get("status", "active"),
                    "current_period_start": current_period_start,
                    "current_period_end": current_period_end,
                    "is_expired": False,
                },
            )

            if not created:
                # Update existing subscription if it wasn't newly created
                subscription_record.plan = plan
                subscription_record.is_active = True
                subscription_record.status = subscription.get("status", "active")
                subscription_record.current_period_start = current_period_start
                subscription_record.current_period_end = current_period_end
                subscription_record.is_expired = False
                subscription_record.save()
                logger.debug(
                    f"Subscription {stripe_subscription_id} updated for agency {agency.name}"
                )
            else:
                logger.debug(
                    f"Subscription {stripe_subscription_id} created for agency {agency.name}"
                )

            logger.info(f"Subscription record handled for agency {agency.name}")

        except Agency.DoesNotExist:
            logger.exception(f"Agency with customer ID {customer_id} does not exist.")
        except Plan.DoesNotExist:
            logger.exception(f"Plan with price ID {plan_id} does not exist.")
        except ValidationError as ve:
            logger.exception(
                f"Validation error while creating/updating subscription: {ve}"
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error while handling subscription creation: {e}"
            )


stripe_webhook = StripeWebhookView.as_view()


class SubscriptionChangeView(
    LoginRequiredMixin, AgencyOwnerRequiredMixin, TemplateView
):
    template_name = "subscriptions/subscription_form_base.html"
    change_type = None  # 'upgrade' or 'downgrade'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not self.change_type:
            raise NotImplementedError("Change type must be defined in subclasses.")

        try:
            profile = user.profile
            agency = profile.agency
            subscription = agency.subscription

            # Check if subscription is active in local DB
            if not subscription.is_active:
                messages.error(
                    request, "Your subscription is not active and cannot be modified."
                )
                logger.warning(
                    f"User {user.username} attempted to modify an inactive subscription."
                )
                context["available_plans"] = []
                return context

            # Retrieve the latest subscription status from Stripe
            stripe_subscription = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )

            # Check if subscription is active in Stripe
            if stripe_subscription["status"] != "active":
                messages.error(
                    request, "Your subscription is not active and cannot be modified."
                )
                logger.warning(
                    f"User {user.username} attempted to modify a Stripe subscription with status {stripe_subscription['status']}."
                )

                # Update local subscription status
                subscription.is_active = False
                subscription.status = stripe_subscription["status"]
                subscription.save()

                context["available_plans"] = []
                return context

            # Determine available plans based on change type
            if self.change_type == "upgrade":
                filtered_plans = Plan.objects.filter(
                    price__gt=subscription.plan.price, is_active=True
                ).order_by("price")
                form_title = "Upgrade Your Subscription"
                button_label = "Upgrade Subscription"
            elif self.change_type == "downgrade":
                filtered_plans = Plan.objects.filter(
                    price__lt=subscription.plan.price, is_active=True
                ).order_by("-price")
                form_title = "Downgrade Your Subscription"
                button_label = "Downgrade Subscription"
            else:
                filtered_plans = []
                form_title = "Change Subscription"
                button_label = "Change Subscription"

            # Group plans by name and billing cycle
            plan_dict = defaultdict(dict)
            for plan in filtered_plans:
                if plan.billing_cycle.lower() == "monthly":
                    plan_dict[plan.name]["monthly_plan"] = plan
                elif plan.billing_cycle.lower() == "yearly":
                    plan_dict[plan.name]["yearly_plan"] = plan

            # Structure available_plans as a list of dictionaries
            available_plans = []
            for plan_name, plans in plan_dict.items():
                if not plans.get("monthly_plan") and not plans.get("yearly_plan"):
                    logger.warning(
                        f"No monthly or yearly plan found for {plan_name}. Skipping."
                    )
                    continue

                description = (
                    plans.get("monthly_plan").description
                    if plans.get("monthly_plan")
                    else plans.get("yearly_plan").description
                )

                available_plans.append(
                    {
                        "name": plan_name,
                        "description": description,
                        "monthly_plan": plans.get("monthly_plan"),
                        "yearly_plan": plans.get("yearly_plan"),
                    }
                )

            context["available_plans"] = available_plans
            context["form_title"] = form_title
            context["button_label"] = button_label

        except Profile.DoesNotExist:
            messages.error(
                self.request, "User profile does not exist. Please contact support."
            )
            logger.error(f"Profile does not exist for user: {user.username}")
        except Subscription.DoesNotExist:
            messages.error(
                self.request, "Active subscription not found. Please subscribe first."
            )
            logger.error(
                f"No active subscription for agency: {agency.name if agency else 'N/A'}"
            )
        except stripe.error.StripeError as e:
            messages.error(
                self.request,
                "An error occurred while retrieving your subscription details. Please try again.",
            )
            logger.exception(f"Stripe error while retrieving subscription: {e}")
        except Exception as e:
            messages.error(
                self.request, "An unexpected error occurred. Please try again."
            )
            logger.exception(f"Unexpected error in SubscriptionChangeView: {e}")

        return context

    def post(self, request, *args, **kwargs):
        if not self.change_type:
            messages.error(request, "Invalid subscription change type.")
            logger.error("SubscriptionChangeView called without a valid change_type.")
            return redirect("subscriptions:subscription_home")

        plan_id = self.kwargs.get("plan_id")  # Get plan_id from URL
        new_plan = get_object_or_404(Plan, id=plan_id, is_active=True)

        user = request.user

        try:
            profile = user.profile
            agency = profile.agency
            subscription = agency.subscription

            # Double-check if subscription is active locally
            if not subscription.is_active:
                messages.error(
                    request, "Your subscription is not active and cannot be modified."
                )
                logger.warning(
                    f"User {user.username} attempted to modify an inactive subscription."
                )
                return redirect("subscriptions:manage_subscription")

            # Retrieve the latest subscription status from Stripe
            stripe_subscription = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )

            # Check if subscription is active in Stripe
            if stripe_subscription["status"] != "active":
                messages.error(
                    request, "Your subscription is not active and cannot be modified."
                )
                logger.warning(
                    f"User {user.username} attempted to modify a Stripe subscription with status {stripe_subscription['status']}."
                )

                # Update local subscription status
                subscription.is_active = False
                subscription.status = stripe_subscription["status"]
                subscription.save()

                return redirect("subscriptions:manage_subscription")

            current_item_id = stripe_subscription["items"]["data"][0].id

            # Modify the subscription in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False,
                items=[
                    {
                        "id": current_item_id,
                        "price": new_plan.stripe_price_id,
                    }
                ],
                proration_behavior="create_prorations",
            )

            # Update local subscription
            subscription.plan = new_plan
            subscription.save()

            action = "upgraded" if self.change_type == "upgrade" else "downgraded"
            messages.success(
                request, f"Subscription {action} to {new_plan.name} plan successfully."
            )
            logger.info(
                f"Subscription {action} to {new_plan.name} by user: {user.username}"
            )
            return redirect("subscriptions:manage_subscription")

        except Subscription.DoesNotExist:
            messages.error(
                request, "Active subscription not found. Please subscribe first."
            )
            logger.error(
                f"No active subscription for agency: {agency.name if agency else 'N/A'}"
            )
            return redirect("subscriptions:subscription_home")
        except stripe.error.StripeError as e:
            messages.error(
                request,
                "An error occurred while changing your subscription. Please try again.",
            )
            logger.exception(f"Stripe error during subscription change: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.exception(f"Unexpected error during subscription change: {e}")
            return redirect("subscriptions:subscription_home")


class UpgradeSubscriptionView(SubscriptionChangeView):
    change_type = "upgrade"


class DowngradeSubscriptionView(SubscriptionChangeView):
    change_type = "downgrade"


class CancelSubscriptionView(LoginRequiredMixin, AgencyOwnerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(
                request, "User profile does not exist. Please contact support."
            )
            logger.error(f"Profile does not exist for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        agency = profile.agency

        if not agency:
            messages.error(
                request,
                "Your agency information is missing. Please contact support.",
            )
            logger.error(f"Agency is None for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        if not agency.stripe_customer_id:
            messages.error(
                request, "No Stripe customer ID found. Please contact support."
            )
            logger.error(f"Stripe customer ID is missing for agency: {agency.name}")
            return redirect("subscriptions:subscription_home")

        try:
            subscriptions = stripe.Subscription.list(
                customer=agency.stripe_customer_id, status="active"
            )

            for subscription in subscriptions.auto_paging_iter():
                stripe.Subscription.delete(subscription.id)
                local_subscription = Subscription.objects.filter(
                    stripe_subscription_id=subscription.id
                ).first()
                if local_subscription:
                    local_subscription.is_active = False
                    local_subscription.status = "canceled"
                    local_subscription.save()
                    logger.info(
                        f"Subscription {subscription.id} deactivated for agency: {agency.name}"
                    )

            messages.success(request, "Your subscription has been cancelled.")
            return redirect("subscriptions:subscription_home")
        except stripe.error.StripeError as e:
            messages.error(request, "Unable to cancel your subscription.")
            logger.exception(f"Stripe error while cancelling subscription: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.exception(f"Unexpected error while cancelling subscription: {e}")
            return redirect("subscriptions:subscription_home")


class ManageSubscriptionView(
    LoginRequiredMixin, AgencyOwnerRequiredMixin, TemplateView
):
    template_name = "subscriptions/manage_subscription.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(
                self.request, "User profile does not exist. Please contact support."
            )
            logger.error(f"Profile does not exist for user: {user.username}")
            return context

        agency = profile.agency

        if not agency:
            messages.error(
                self.request,
                "Your agency information is missing. Please contact support.",
            )
            logger.error(f"Agency is None for user: {user.username}")
            return context

        if not agency.stripe_customer_id:
            messages.error(
                self.request, "No Stripe customer ID found. Please contact support."
            )
            logger.error(f"Stripe customer ID is missing for agency: {agency.name}")
            return context

        try:
            # Fetch subscription from local database
            try:
                subscription = agency.subscription
                if (
                    subscription.is_active
                    and subscription.current_period_end
                    and subscription.current_period_end > timezone.now()
                ):
                    context["subscription"] = subscription
                else:
                    context["subscription"] = None
            except Subscription.DoesNotExist:
                context["subscription"] = None
                logger.warning(f"No active subscription for agency: {agency.name}")

            # Fetch subscriptions from Stripe
            subscriptions = stripe.Subscription.list(
                customer=agency.stripe_customer_id, limit=10
            )
            context["subscriptions"] = subscriptions

            # Generate Billing Portal session link
            billing_portal_session = stripe.billing_portal.Session.create(
                customer=agency.stripe_customer_id,
                return_url=self.request.build_absolute_uri(
                    reverse("subscriptions:manage_subscription")
                ),
            )
            context["billing_portal_url"] = billing_portal_session.url

            # Determine available plans for upgrade and downgrade
            if subscription and subscription.is_active:
                current_plan = subscription.plan
                # For upgrade: plans with higher price
                upgrade_plans = Plan.objects.filter(
                    price__gt=current_plan.price, is_active=True
                ).order_by("price")
                # For downgrade: plans with lower price
                downgrade_plans = Plan.objects.filter(
                    price__lt=current_plan.price, is_active=True
                ).order_by("-price")
                context["upgrade_plans"] = upgrade_plans
                context["downgrade_plans"] = downgrade_plans
            else:
                context["upgrade_plans"] = Plan.objects.filter(is_active=True).order_by(
                    "price"
                )
                context["downgrade_plans"] = []

        except stripe.error.StripeError as e:
            messages.error(self.request, "Unable to retrieve subscription details.")
            logger.exception(f"Stripe error while retrieving subscriptions: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(
                self.request, "An unexpected error occurred. Please try again."
            )
            logger.exception(f"Unexpected error while retrieving subscriptions: {e}")
            return redirect("subscriptions:subscription_home")

        return context


class UpdatePaymentMethodView(LoginRequiredMixin, AgencyOwnerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(
                request, "User profile does not exist. Please contact support."
            )
            logger.error(f"Profile does not exist for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        agency = profile.agency

        if not agency:
            messages.error(
                request, "Your agency information is missing. Please contact support."
            )
            logger.error(f"Agency is None for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        if not agency.stripe_customer_id:
            messages.error(
                request, "No Stripe customer ID found. Please contact support."
            )
            logger.error(f"Stripe customer ID is missing for agency: {agency.name}")
            return redirect("subscriptions:subscription_home")

        try:
            session = stripe.billing_portal.Session.create(
                customer=agency.stripe_customer_id,
                return_url=self.request.build_absolute_uri(
                    reverse("subscriptions:manage_subscription")
                ),
            )
            logger.info(
                f"Billing Portal session created: {session.id} for agency: {agency.name}"
            )
            return redirect(session.url)
        except stripe.error.StripeError as e:
            messages.error(request, "Unable to redirect to Billing Portal.")
            logger.exception(f"Stripe error while creating Billing Portal session: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.exception(
                f"Unexpected error while creating Billing Portal session: {e}"
            )
            return redirect("subscriptions:subscription_home")
