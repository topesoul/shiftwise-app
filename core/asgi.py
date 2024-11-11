# /workspace/shiftwise/asgi.py

import os
import django
from channels.routing import get_default_application

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import shifts.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shiftwise.settings")
django.setup()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(shifts.routing.websocket_urlpatterns)
        ),
    }
)
