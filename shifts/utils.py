import requests
from django.conf import settings

def get_address_from_postcode(postcode):
    """
    This function uses the OS Places API to get address information from a given postcode.
    
    :param postcode: A valid UK postcode
    :return: A dictionary containing address information (address_line1, city, county, country, latitude, longitude)
    """
    url = f"https://api.os.uk/search/places/v1/postcode?postcode={postcode}&key={settings.API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Check if there are results
        if data['results']:
            result = data['results'][0]
            address = {
                'address_line1': result['DPA'].get('ADDRESS', ''),
                'postcode': result['DPA'].get('POSTCODE', ''),
                'city': result['DPA'].get('POST_TOWN', ''),
                'county': result['DPA'].get('COUNTY', ''),
                'country': result['DPA'].get('COUNTRY', 'UK'),
                'latitude': result['DPA'].get('LATITUDE', None),
                'longitude': result['DPA'].get('LONGITUDE', None),
            }
            return address
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching address from postcode: {e}")
        return None