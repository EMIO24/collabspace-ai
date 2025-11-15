"""
ASGI config for collabspace_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

"""
ASGI config for CollabSpace AI project.

It exposes the ASGI callable as a module-level variable named ``application``.

This configuration supports both HTTP and WebSocket connections.
"""

"""
ASGI config for CollabSpace AI project.

It exposes the ASGI callable as a module-level variable named ``application``.

This configuration supports both HTTP and WebSocket connections.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collabspace_backend.settings')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django initialization
from apps.messaging.routing import websocket_urlpatterns

# ASGI application with support for HTTP and WebSocket
application = ProtocolTypeRouter({
    # Handle traditional HTTP requests
    "http": django_asgi_app,
    
    # Handle WebSocket connections
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})