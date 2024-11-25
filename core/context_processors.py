# shiftwise/context_processors.py

from django.conf import settings


def google_places_api_key(request):
    return {"GOOGLE_PLACES_API_KEY": settings.GOOGLE_PLACES_API_KEY}
