from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    IntegrationViewSet,
    WebhookViewSet,
    GitHubOAuthCallback,
    GitHubWebhookReceiver,
    SlackWebhookReceiver,
)

app_name = "integrations"

# -------------------------
# DRF Router for ViewSets
# -------------------------
router = DefaultRouter()
router.register(r'integrations', IntegrationViewSet, basename='integrations')
router.register(r'webhooks', WebhookViewSet, basename='webhooks')

# -------------------------
# URL Patterns
# -------------------------
urlpatterns = [
    # OAuth callbacks
    path('oauth/github/callback/', GitHubOAuthCallback.as_view(), name='github-oauth-callback'),

    # Webhook receivers
    path('webhooks/github/', GitHubWebhookReceiver.as_view(), name='github-webhook-receiver'),
    path('webhooks/slack/', SlackWebhookReceiver.as_view(), name='slack-webhook-receiver'),
]

# Include the DRF router URLs
urlpatterns += router.urls
