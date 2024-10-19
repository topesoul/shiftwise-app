from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
import logging

# Initialize logger
logger = logging.getLogger(__name__)

def get_address_from_postcode(postcode):
    """
    Fetches address details based on the provided postcode using Geopy's Nominatim geocoder.
    
    :param postcode: A valid UK postcode
    :return: A dictionary containing address information (address_line1, city, state, country, latitude, longitude)
    """
    geolocator = Nominatim(user_agent="shiftwise_app")
    try:
        location = geolocator.geocode(postcode, exactly_one=True, timeout=10, country_codes='gb')
        if location:
            address = location.raw.get('address', {})
            return {
                'address_line1': f"{address.get('road', '')} {address.get('house_number', '')}".strip(),
                'postcode': address.get('postcode', ''),
                'city': address.get('city') or address.get('town') or address.get('village', ''),
                'state': address.get('county', ''),
                'country': address.get('country', 'UK'),
                'latitude': location.latitude,
                'longitude': location.longitude,
            }
        
        logger.warning(f"No results found for postcode: {postcode}")
        return None

    except GeocoderServiceError as e:
        logger.error(f"Error fetching address from postcode: {e}")
        return None