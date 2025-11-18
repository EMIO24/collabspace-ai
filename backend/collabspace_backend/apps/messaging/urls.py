from django.urls import path, include
from rest_framework_nested import routers
from . import views

# Standard Router for top-level resources
router = routers.SimpleRouter()
router.register(r'channels', views.ChannelViewSet, basename='channel')
router.register(r'dms', views.DirectMessageViewSet, basename='direct-message')

# Nested Router for messages belonging to a channel
channels_router = routers.NestedSimpleRouter(router, r'channels', lookup='channel')
channels_router.register(r'messages', views.MessageViewSet, basename='channel-message')

# The nested router automatically handles:
# GET /channels/{channel_pk}/messages/
# POST /channels/{channel_pk}/messages/
# GET /channels/{channel_pk}/messages/{pk}/
# ... and actions defined on MessageViewSet

urlpatterns = [
    # Main Channel and DM routes (includes actions like /channels/{pk}/archive/)
    path('', include(router.urls)),
    
    # Nested Channel Message routes
    path('', include(channels_router.urls)),

    # Search route: /api/messaging/search/?q=query&channel_id=uuid
    path('search/', views.MessageSearchView.as_view(), name='message-search'),
    
    # DM mark-as-read action: /api/messaging/dms/mark-as-read/
    # Handled automatically by the router for DirectMessageViewSet
]