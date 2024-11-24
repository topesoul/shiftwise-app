# /workspace/shiftwise/subscriptions/utils.py

import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Stripe with the secret key from settings
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_customer(agency):
    """
    Creates a Stripe customer for the given agency.
    If a customer with the same email exists, returns the existing customer.

    Parameters:
    - agency (Agency): The agency instance for which to create a Stripe customer.

    Returns:
    - stripe.Customer: The created or existing Stripe customer.
    """
    try:
        # Search for existing customer by email
        customers = stripe.Customer.list(email=agency.email, limit=1)
        if customers.data:
            customer = customers.data[0]
            logger.info(
                f"Existing Stripe customer found: {customer.id} for agency: {agency.name}"
            )
            return customer

        # Create new customer if none exists
        customer = stripe.Customer.create(
            name=agency.name,
            email=agency.email,
            metadata={
                "agency_id": agency.id,
            },
        )
        logger.info(f"Stripe customer created: {customer.id} for agency: {agency.name}")
        return customer
    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error while creating customer: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while creating Stripe customer: {e}")
        raise
