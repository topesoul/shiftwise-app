# /workspace/shiftwise/subscriptions/utils.py

import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe with the Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_customer(agency):
    """
    Creates a Stripe customer for the given agency.

    Args:
        agency (Agency): The agency instance for which to create the Stripe customer.

    Returns:
        stripe.Customer: The created Stripe customer object.
    """
    try:
        customer = stripe.Customer.create(
            email=agency.email,
            name=agency.name,
            metadata={
                "agency_id": agency.id,
                "agency_code": agency.agency_code,
            },
        )
        logger.info(f"Stripe customer created for agency {agency.name} with ID {customer.id}.")
        return customer
    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error while creating customer for agency {agency.name}: {e}")
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error while creating Stripe customer for agency {agency.name}: {e}")
        raise e