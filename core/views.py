# /workspace/shiftwise/core/views.py
import logging
import requests
from django.http import JsonResponse, HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

def google_maps_proxy(request):
    """
    Proxies requests to the Google Maps API to hide the API key.
    """
    api_key = settings.GOOGLE_PLACES_API_KEY
    params = request.GET.copy()
    params["key"] = api_key

    try:
        response = requests.get("https://maps.googleapis.com/maps/api/js", params=params)

        if response.status_code == 200:
            # Ensure we return the JavaScript content type
            return HttpResponse(response.content, content_type="application/javascript")
        else:
            logger.error(f"Google Maps API Error: {response.text}")
            return JsonResponse(
                {"error": "Failed to fetch Google Maps API"}, status=response.status_code
            )
    except Exception as e:
        logger.exception(f"Error in google_maps_proxy: {str(e)}")
        return JsonResponse({"error": "An error occurred"}, status=500)
