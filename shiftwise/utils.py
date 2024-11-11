# /workspace/shiftwise/shifts/utils.py

from django.db.models import F, FloatField
from django.db.models.functions import Cast
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
import logging, requests
from shifts.models import Shift
from accounts.models import User

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2, unit="miles"):
    """
    Calculates the great-circle distance between two points
    on the Earth specified by latitude/longitude using the Haversine formula.
    """
    from math import radians, sin, cos, sqrt, atan2

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 3956 if unit == "miles" else 6371  # Radius of Earth in miles or kilometers
    return c * r


def predict_staffing_needs(date):
    """
    Function for predicting staffing needs.
    Implement integrate a machine learning model here.
    """
    return 5


def generate_shift_code():
    """
    Generates a unique shift code using UUID4.
    """
    return f"SHIFT-{uuid.uuid4().hex[:8].upper()}"


def get_shift_assignment_queryset(user):
    """
    Retrieves a queryset of ShiftAssignments based on user permissions.
    """
    if user.is_superuser:
        return ShiftAssignment.objects.all()
    elif user.groups.filter(name="Agency Managers").exists():
        return ShiftAssignment.objects.filter(shift__agency=user.profile.agency)
    elif user.groups.filter(name="Agency Staff").exists():
        return ShiftAssignment.objects.filter(worker=user)
    else:
        return ShiftAssignment.objects.none()


def auto_assign_shifts():
    """
    Auto-assigns available shifts to workers based on their preferences.
    """
    unassigned_shifts = Shift.objects.filter(is_completed=False).exclude(
        assignments__isnull=False
    )

    for shift in unassigned_shifts:
        if not shift.latitude or not shift.longitude:
            logger.warning(f"Shift {shift.id} does not have valid geolocation data.")
            continue

        # Fetch workers who prefer the shift timing and are within travel distance
        workers = (
            User.objects.filter(
                groups__name="Agency Staff",
                is_active=True,
                profile__latitude__isnull=False,
                profile__longitude__isnull=False,
                profile__agency=shift.agency,
            )
            .annotate(
                distance=Cast(
                    haversine_distance(
                        F("profile__latitude"),
                        F("profile__longitude"),
                        shift.latitude,
                        shift.longitude,
                        "miles",
                    ),
                    FloatField(),
                )
            )
            .filter(Q(profile__travel_radius__gte=F("distance")))
            .order_by("shift_assignments__count")
        )

        if workers.exists():
            worker = workers.first()
            ShiftAssignment.objects.create(shift=shift, worker=worker)
            logger.info(f"Auto-assigned Shift ID {shift.id} to Worker {worker.username}.")
        else:
            logger.warning(f"No suitable workers found for Shift ID {shift.id}.")


def get_address_from_address_line1(address_line1):
    """
    Fetches address details based on the given address line 1 using Google Geocoding API.

    Args:
        address_line1 (str): The first line of the address to geocode.

    Returns:
        list: A list of address dictionaries containing address components, latitude, and longitude.
    """
    GOOGLE_GEOCODING_API_KEY = settings.GOOGLE_GEOCODING_API_KEY
    if not GOOGLE_GEOCODING_API_KEY:
        logger.error("Google Geocoding API key not found in environment variables.")
        raise ValueError("Google Geocoding API key not found in environment variables.")

    # Check if the address is cached
    cache_key = f"geocode_{address_line1}"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Cache hit for address_line1: {address_line1}")
        return cached_data

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address_line1,
        "key": GOOGLE_GEOCODING_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.exception(
            f"RequestException while fetching geocoding data for address_line1 {address_line1}: {e}"
        )
        return []

    try:
        data = response.json()
    except ValueError as e:
        logger.exception(f"JSON decoding failed for address_line1 {address_line1}: {e}")
        return []

    if data.get("status") != "OK":
        logger.warning(
            f"Geocoding API returned status {data.get('status')} for address_line1 {address_line1}"
        )
        return []

    results = data.get("results", [])
    addresses = []
    for result in results:
        address_components = result.get("address_components", [])
        address = {}
        for component in address_components:
            types = component.get("types", [])
            if "street_number" in types:
                address["street_number"] = component.get("long_name", "")
            if "route" in types:
                address["route"] = component.get("long_name", "")
            if "locality" in types or "postal_town" in types:
                address["city"] = component.get("long_name", "")
            if "administrative_area_level_2" in types:
                address["county"] = component.get("long_name", "")
            if "administrative_area_level_1" in types:
                address["state"] = component.get("long_name", "")
            if "country" in types:
                address["country"] = component.get("long_name", "")
            if "postal_code" in types:
                address["postcode"] = component.get("long_name", "")

        address_line1_combined = (
            f"{address.get('street_number', '')} {address.get('route', '')}".strip()
        )
        city = address.get("city", "")
        county = address.get("county", "")
        state = address.get("state", "")
        country = address.get("country", "")
        postcode_result = address.get("postcode", "")
        latitude = result["geometry"]["location"]["lat"]
        longitude = result["geometry"]["location"]["lng"]

        addresses.append(
            {
                "address_line1": address_line1_combined,
                "address_line2": "",
                "city": city,
                "county": county,
                "state": state,
                "country": country,
                "postcode": postcode_result,
                "latitude": latitude,
                "longitude": longitude,
            }
        )

    # Cache the result for 24 hours
    cache.set(cache_key, addresses, timeout=60 * 60 * 24)
    logger.debug(f"Cached geocoding data for address_line1: {address_line1}")
    return addresses