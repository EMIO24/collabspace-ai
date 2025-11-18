from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

app_name = 'messaging'

router = DefaultRouter()
router.register('channels', ChannelViewSet, basename='channel')
router.register('messages', MessageViewSet, basename='message')
router.register('direct-messages', DirectMessageViewSet, basename='direct-message')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', MessageSearchView.as_view(), name='message-search'),
]