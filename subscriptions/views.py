# /workspace/shiftwise/subscriptions/views.py

import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from subscriptions.models import Plan, Subscription
from accounts.models import Profile, Agency
from accounts.forms import UpdateProfileForm
from .utils import create_stripe_customer

# Initialize logger
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionHomeView(LoginRequiredMixin, TemplateView):
    """
    Displays the available subscription plans and the user's current subscription status.
    """
    template_name = "subscriptions/subscription_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        # Ensure the user has a profile
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(self.request, "User profile does not exist. Please contact support.")
            logger.error(f"Profile does not exist for user: {user.username}")
            return context

        agency = getattr(profile, 'agency', None)

        if agency is None:
            messages.error(self.request, "Your agency information is missing. Please contact support.")
            logger.error(f"Agency is None for user: {user.username}")
            return context

        # Retrieve all active plans
        plans = Plan.objects.filter(is_active=True).order_by("name", "billing_cycle")

        # Group plans by name and billing cycle
        plan_dict = {}
        for plan in plans:
            plan_group = plan_dict.setdefault(plan.name, {
                'name': plan.name,
                'description': plan.description,
                'monthly_plan': None,
                'yearly_plan': None
            })
            if plan.billing_cycle == 'monthly':
                plan_group['monthly_plan'] = plan
            elif plan.billing_cycle == 'yearly':
                plan_group['yearly_plan'] = plan

        # Convert plan_dict to a list
        available_plans = list(plan_dict.values())

        context["available_plans"] = available_plans

        # Get current subscription
        subscription = Subscription.objects.filter(
            agency=agency, is_active=True, current_period_end__gt=timezone.now()
        ).first()
        context["subscription"] = subscription

        return context


class SubscribeView(LoginRequiredMixin, View):
    """
    Handles the subscription process, integrating with Stripe Checkout.
    """

    def post(self, request, plan_id, *args, **kwargs):
        user = request.user

        # Ensure the user has a profile
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(request, "User profile does not exist. Please contact support.")
            logger.error(f"Profile does not exist for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        agency = getattr(profile, 'agency', None)

        if agency is None:
            messages.error(request, "Your agency information is missing. Please contact support.")
            logger.error(f"Agency is None for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        # Get the selected plan
        plan = get_object_or_404(Plan, id=plan_id, is_active=True)

        # Create or retrieve a Stripe Customer
        if not hasattr(agency, 'stripe_customer_id') or not agency.stripe_customer_id:
            try:
                # Use the Utility Function to Create Stripe Customer
                customer = create_stripe_customer(agency)
                # Save the returned customer ID to the agency
                agency.stripe_customer_id = customer.id
                agency.save()
                logger.info(f"Stripe customer created for agency: {agency.name}, Customer ID: {customer.id}")
            except stripe.error.StripeError as e:
                messages.error(request, "There was an error with Stripe. Please try again.")
                logger.exception(f"Stripe error while creating customer: {e}")
                return redirect("subscriptions:subscription_home")
            except Exception as e:
                messages.error(request, "An unexpected error occurred. Please try again.")
                logger.exception(f"Unexpected error while creating customer: {e}")
                return redirect("subscriptions:subscription_home")
        else:
            try:
                # Retrieve Existing Stripe Customer
                customer = stripe.Customer.retrieve(agency.stripe_customer_id)
                logger.info(f"Stripe customer retrieved for agency: {agency.name}, Customer ID: {customer.id}")
            except stripe.error.StripeError as e:
                messages.error(request, "Failed to retrieve Stripe customer.")
                logger.exception(f"Stripe error while retrieving customer: {e}")
                return redirect("subscriptions:subscription_home")
            except Exception as e:
                messages.error(request, "An unexpected error occurred. Please try again.")
                logger.exception(f"Unexpected error while retrieving customer: {e}")
                return redirect("subscriptions:subscription_home")

        # Create a Stripe Checkout Session
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
                success_url=request.build_absolute_uri(reverse("subscriptions:subscription_success")),
                cancel_url=request.build_absolute_uri(reverse("subscriptions:subscription_cancel")),
            )
            logger.info(f"Stripe Checkout Session created: {checkout_session.id} for agency: {agency.name}")
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
    """
    Renders the subscription success page.
    """
    messages.success(request, "Your subscription was successful!")
    return render(request, "subscriptions/success.html")


def subscription_cancel(request):
    """
    Renders the subscription cancellation page.
    """
    messages.error(request, "Your subscription was cancelled.")
    return render(request, "subscriptions/cancel.html")


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Handles incoming Stripe webhooks.
    """

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            logger.info(f"Stripe webhook received: {event.type}")
        except ValueError as e:
            # Invalid payload
            logger.exception(f"Invalid payload: {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.exception(f"Invalid signature: {e}")
            return HttpResponse(status=400)

        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            self.handle_checkout_session_completed(session)
        elif event.type == 'invoice.paid':
            invoice = event.data.object
            self.handle_invoice_paid(invoice)
        elif event.type == 'customer.subscription.deleted':
            subscription = event.data.object
            self.handle_subscription_deleted(subscription)
        # Add more event types as needed

        return HttpResponse(status=200)

    def handle_checkout_session_completed(self, session):
        """
        Handles the checkout.session.completed event.
        """
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        # Note: 'display_items' is deprecated in Stripe. Use 'line_items' instead.
        try:
            line_items = stripe.checkout.Session.list_line_items(session.id, limit=1)
            plan_id = line_items.data[0].price.id if line_items.data else None
        except stripe.error.StripeError as e:
            logger.exception(f"Error retrieving line items: {e}")
            return

        if not plan_id:
            logger.error("No plan_id found in checkout session.")
            return

        try:
            agency = Agency.objects.get(stripe_customer_id=customer_id)
            plan = Plan.objects.get(stripe_price_id=plan_id)
            subscription = Subscription.objects.create(
                agency=agency,
                plan=plan,
                stripe_subscription_id=subscription_id,
                is_active=True,
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timezone.timedelta(days=30),  # Adjust based on plan
            )
            # Deactivate any old subscriptions
            Subscription.objects.filter(agency=agency).exclude(id=subscription.id).update(is_active=False)
            logger.info(f"Subscription created for agency {agency.name}, Subscription ID: {subscription_id}")
        except Agency.DoesNotExist:
            logger.exception(f"Agency with customer ID {customer_id} does not exist.")
        except Plan.DoesNotExist:
            logger.exception(f"Plan with price ID {plan_id} does not exist.")
        except Exception as e:
            logger.exception(f"Unexpected error while handling checkout session: {e}")

    def handle_invoice_paid(self, invoice):
        """
        Handles the invoice.paid event.
        """
        # Implement logic to handle successful invoice payment
        logger.info(f"Invoice paid: {invoice.id}")
        # Example: Update subscription status or notify the user
        pass

    def handle_subscription_deleted(self, subscription):
        """
        Handles the customer.subscription.deleted event.
        """
        stripe_subscription_id = subscription.get('id')
        try:
            local_subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
            local_subscription.is_active = False
            local_subscription.save()
            logger.info(f"Subscription {stripe_subscription_id} deactivated.")
        except Subscription.DoesNotExist:
            logger.exception(f"Subscription with ID {stripe_subscription_id} does not exist.")
        except Exception as e:
            logger.exception(f"Unexpected error while handling subscription deletion: {e}")


stripe_webhook = StripeWebhookView.as_view()


class ManageSubscriptionView(LoginRequiredMixin, TemplateView):
    """
    Allows users to manage their subscriptions.
    """
    template_name = "subscriptions/manage_subscription.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Ensure the user has a profile
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(self.request, "User profile does not exist. Please contact support.")
            logger.error(f"Profile does not exist for user: {user.username}")
            return context

        agency = getattr(profile, 'agency', None)

        if agency is None:
            messages.error(self.request, "Your agency information is missing. Please contact support.")
            logger.error(f"Agency is None for user: {user.username}")
            return context

        if not hasattr(agency, 'stripe_customer_id') or not agency.stripe_customer_id:
            messages.error(self.request, "No Stripe customer ID found. Please contact support.")
            logger.error(f"Stripe customer ID is missing for agency: {agency.name}")
            return context

        try:
            subscriptions = stripe.Subscription.list(customer=agency.stripe_customer_id)
            context['subscriptions'] = subscriptions
            logger.info(f"Retrieved subscriptions for agency: {agency.name}")
        except stripe.error.StripeError as e:
            messages.error(self.request, "Unable to retrieve subscription details.")
            logger.exception(f"Stripe error while retrieving subscriptions: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(self.request, "An unexpected error occurred. Please try again.")
            logger.exception(f"Unexpected error while retrieving subscriptions: {e}")
            return redirect("subscriptions:subscription_home")

        return context


class CancelSubscriptionView(LoginRequiredMixin, View):
    """
    Allows users to cancel their subscription.
    """

    def post(self, request, *args, **kwargs):
        user = request.user

        # Ensure the user has a profile
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(request, "User profile does not exist. Please contact support.")
            logger.error(f"Profile does not exist for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        agency = getattr(profile, 'agency', None)

        if agency is None:
            messages.error(request, "Your agency information is missing. Please contact support.")
            logger.error(f"Agency is None for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        if not hasattr(agency, 'stripe_customer_id') or not agency.stripe_customer_id:
            messages.error(request, "No Stripe customer ID found. Please contact support.")
            logger.error(f"Stripe customer ID is missing for agency: {agency.name}")
            return redirect("subscriptions:subscription_home")

        try:
            subscriptions = stripe.Subscription.list(customer=agency.stripe_customer_id)
            for subscription in subscriptions.auto_paging_iter():
                stripe.Subscription.delete(subscription.id)
                # Update local subscription record
                local_subscription = Subscription.objects.filter(
                    stripe_subscription_id=subscription.id
                ).first()
                if local_subscription:
                    local_subscription.is_active = False
                    local_subscription.save()
                    logger.info(f"Subscription {subscription.id} deactivated for agency: {agency.name}")
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


class UpdatePaymentMethodView(LoginRequiredMixin, View):
    """
    Allows users to update their payment method.
    """

    def get(self, request, *args, **kwargs):
        """
        Renders a page with a link to Stripe's Billing Portal.
        """
        user = request.user

        # Ensure the user has a profile
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            messages.error(request, "User profile does not exist. Please contact support.")
            logger.error(f"Profile does not exist for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        agency = getattr(profile, 'agency', None)

        if agency is None:
            messages.error(request, "Your agency information is missing. Please contact support.")
            logger.error(f"Agency is None for user: {user.username}")
            return redirect("subscriptions:subscription_home")

        if not hasattr(agency, 'stripe_customer_id') or not agency.stripe_customer_id:
            messages.error(request, "No Stripe customer ID found. Please contact support.")
            logger.error(f"Stripe customer ID is missing for agency: {agency.name}")
            return redirect("subscriptions:subscription_home")

        try:
            billing_portal_session = stripe.billing_portal.Session.create(
                customer=agency.stripe_customer_id,
                return_url=request.build_absolute_uri(reverse("subscriptions:subscription_home")),
            )
            logger.info(f"Billing portal session created for agency: {agency.name}, Session ID: {billing_portal_session.id}")
            return redirect(billing_portal_session.url)
        except stripe.error.StripeError as e:
            messages.error(request, "Unable to update your payment method.")
            logger.exception(f"Stripe error while creating billing portal session: {e}")
            return redirect("subscriptions:subscription_home")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            logger.exception(f"Unexpected error while creating billing portal session: {e}")
            return redirect("subscriptions:subscription_home")