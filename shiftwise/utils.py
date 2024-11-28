# /workspace/shiftwise/shiftwise/utils.py

import hashlib
import logging
import uuid
from math import atan2, cos, radians, sin, sqrt

from django.conf import settings
from django.core.cache import cache
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import GoogleV3

from accounts.models import User
from shifts.models import ShiftAssignment

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2, unit="miles"):
    """
    Calculates the great-circle distance between two points
    on the Earth specified by latitude/longitude using the Haversine formula.
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 3956 if unit == "miles" else 6371  # Earth radius in miles or kilometers
    distance = c * r
    logger.debug(
        f"Haversine distance calculated: {distance} {unit} between points "
        f"({lat1}, {lon1}) and ({lat2}, {lon2})"
    )
    return distance


def generate_shift_code():
    """
    Generates a unique shift code using UUID4.
    """
    shift_code = f"SHIFT-{uuid.uuid4().hex[:8].upper()}"
    logger.debug(f"Generated shift code: {shift_code}")
    return shift_code


def generate_unique_code(prefix="CODE-", length=8):
    """
    Generates a unique code with a given prefix and length.
    Ensures uniqueness by checking existing codes in the database.
    """
    while True:
        code = f"{prefix}{uuid.uuid4().hex[:length].upper()}"
        # Check uniqueness against a relevant model field
        if not User.objects.filter(username=code).exists():
            logger.debug(f"Generated unique code: {code}")
            return code


def generate_cache_key(address):
    """
    Generates a safe cache key by hashing the address.
    """
    hash_object = hashlib.sha256(address.encode("utf-8"))
    hex_dig = hash_object.hexdigest()
    cache_key = f"geocode_{hex_dig}"
    logger.debug(f"Generated cache key: {cache_key} for address: {address}")
    return cache_key


def geocode_address(address):
    """
    Geocodes an address using Google Geocoding API via geopy and caches the result.

    Args:
        address (str): The address to geocode.

    Returns:
        dict: A dictionary containing 'latitude' and 'longitude'.

    Raises:
        Exception: If geocoding fails.
    """
    cache_key = generate_cache_key(address)
    geocode = cache.get(cache_key)
    if geocode:
        logger.debug(f"Cache hit for address: {address}")
        return geocode

    if not settings.GOOGLE_PLACES_API_KEY:
        logger.error("Google Geocoding API key not found in settings.")
        raise ValueError("Google Geocoding API key not configured.")

    try:
        geolocator = GoogleV3(api_key=settings.GOOGLE_PLACES_API_KEY)
        location = geolocator.geocode(address, timeout=10)
        if location:
            geocode = {
                "latitude": location.latitude,
                "longitude": location.longitude,
            }
            cache.set(cache_key, geocode, timeout=86400)  # Cache for 1 day
            logger.info(f"Geocoded and cached address: {address}")
            return geocode
        else:
            logger.error(f"Could not geocode address: {address}")
            raise Exception("Could not geocode address.")
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.exception(f"Geocoding service error for address '{address}': {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error geocoding address '{address}': {e}")
        raise


def get_shift_assignment_queryset(user):
    """
    Retrieves a queryset of ShiftAssignments based on user permissions.

    Args:
        user (User): The user requesting the shift assignments.

    Returns:
        QuerySet: A Django QuerySet of ShiftAssignments.
    """
    if user.is_superuser:
        logger.debug(f"Superuser {user.username} accessing all shift assignments.")
        return ShiftAssignment.objects.all()
    elif user.groups.filter(name="Agency Managers").exists():
        logger.debug(
            f"Agency Manager {user.username} accessing agency shift assignments."
        )
        return ShiftAssignment.objects.filter(shift__agency=user.profile.agency)
    elif user.groups.filter(name="Agency Staff").exists():
        logger.debug(f"Agency Staff {user.username} accessing their shift assignments.")
        return ShiftAssignment.objects.filter(worker=user)
    else:
        logger.debug(
            f"User {user.username} has no permissions to access shift assignments."
        )
        return ShiftAssignment.objects.none()


def get_address_from_address_line1(address_line1):
    """
    Fetches address details based on the given address line 1 using Google Geocoding API.

    Args:
        address_line1 (str): The first line of the address to geocode.

    Returns:
        list: A list of address dictionaries containing address components, latitude, and longitude.
    """
    if not settings.GOOGLE_PLACES_API_KEY:
        logger.error("Google Geocoding API key not found in settings.")
        raise ValueError("Google Geocoding API key not configured.")

    # Check if the address is cached
    cache_key = generate_cache_key(address_line1)
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Cache hit for address_line1: {address_line1}")
        return cached_data

    try:
        geolocator = GoogleV3(api_key=settings.GOOGLE_PLACES_API_KEY)
        location = geolocator.geocode(address_line1, timeout=10)
        if not location:
            logger.warning(
                f"No results from Geocoding API for address_line1: {address_line1}"
            )
            return []
        address = {
            "address_line1": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        cache.set(cache_key, [address], timeout=86400)  # Cache for 1 day
        logger.info(f"Geocoded and cached address_line1: {address_line1}")
        return [address]
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.exception(
            f"Geocoding service error for address_line1 '{address_line1}': {e}"
        )
        return []
    except Exception as e:
        logger.exception(
            f"Unexpected error fetching address from address_line1 '{address_line1}': {e}"
        )
        return []
