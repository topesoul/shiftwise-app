# shifts/utils.py

import os
import requests
import logging

logger = logging.getLogger(__name__)

def get_address_from_postcode(postcode):
    api_key = os.environ.get('PLACES_API_KEY')
    if not api_key:
        logger.error('PLACES_API_KEY not set in environment variables.')
        return None

    url = f"https://api.os.uk/search/places/v1/postcode?postcode={postcode}&key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        # Parse the data to extract address components
        if data.get('results'):
            address = data['results'][0].get('DPA', {})
            return {
                'address_line1': address.get('ADDRESS', ''),
                'city': address.get('POST_TOWN', ''),
                'state': address.get('COUNTY', ''),
                'postcode': address.get('POSTCODE', ''),
                'country': 'UK',
                'latitude': address.get('LATITUDE', ''),
                'longitude': address.get('LONGITUDE', ''),
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching address for postcode {postcode}: {e}")
    except KeyError as e:
        logger.error(f"Unexpected response structure: Missing key {e}")
    return None
