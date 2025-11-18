from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Path captures the workspace ID for context-specific group management
    re_path(r'ws/workspace/(?P<workspace_id>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
]