"""
ASGI config for aprendecomigo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aprendecomigo.settings")

# Initialize Django ASGI application early to ensure the app is loaded
# before code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import after Django is initialized
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from classroom.consumers import ChatConsumer
from django.urls import path

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter([
                    # Only chat functionality uses websockets
                    path("ws/chat/<str:channel_name>/", ChatConsumer.as_asgi()),
                ])
            )
        ),
    }
)
