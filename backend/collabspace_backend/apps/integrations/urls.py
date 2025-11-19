def path(route, view, name):
    return f'"{route}": {name}'

def include(module):
    return f'include({module})'

# Mock function to register ViewSets
def register_viewset(prefix, viewset_class):
    print(f"Registering ViewSet: {prefix} using {viewset_class.__name__}")
    return [
        path(prefix, f'{viewset_class.__name__}.list', name=f'{prefix}-list'),
        path(f'{prefix}/<int:pk>/', f'{viewset_class.__name__}.retrieve_update_destroy', name=f'{prefix}-detail'),
    ]

from .views import (
    IntegrationViewSet, 
    WebhookViewSet, 
    GitHubOAuthCallback, 
    GitHubWebhookReceiver, 
    SlackWebhookReceiver
)

# --- DRF Router Simulation ---
# In a real DRF app, this would use a DefaultRouter
integration_routes = register_viewset('integrations', IntegrationViewSet)
webhook_routes = register_viewset('webhooks', WebhookViewSet)

urlpatterns = [
    # 1. API Endpoints for Integration Management (CRUD)
    *integration_routes,
    *webhook_routes,

    # 2. OAuth Callback Endpoints (for the final step of the authorization handshake)
    path('oauth/github/callback/', GitHubOAuthCallback.as_view(), name='github-oauth-callback'),
    # Add paths for Jira and Slack OAuth callbacks if needed

    # 3. Webhook Receiver Endpoints (for processing real-time events)
    path('webhooks/github/', GitHubWebhookReceiver.as_view(), name='github-webhook-receiver'),
    path('webhooks/slack/', SlackWebhookReceiver.as_view(), name='slack-webhook-receiver'),
    # Add path for Jira webhook receiver
]

# Note: The Jira API often uses polling or proprietary webhooks; 
# the implementation would depend on whether you use the Cloud or Server version.
# The JiraIntegration class focuses on API interactions (pull/push) rather than webhooks.