from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    # Requires an authenticated user and workspace_id in the URL
    re_path(r'ws/workspace/(?P<workspace_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]