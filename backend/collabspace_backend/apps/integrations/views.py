from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from .models import Integration, Webhook
from .github import GitHubIntegration, GitHubIntegrationError
from .slack import SlackIntegration
from .jira import JiraIntegrationError

logger = logging.getLogger(__name__)

# -------------------------
# Integration ViewSet
# -------------------------
class IntegrationViewSet(ViewSet):
    """CRUD operations on Integrations."""

    def list(self, request):
        integrations = Integration.objects.all()
        data = [i.to_dict() for i in integrations]  # Ensure Integration has to_dict
        return Response({'data': data}, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            integration = Integration.objects.get(pk=pk)
            return Response({'data': integration.to_dict()}, status=status.HTTP_200_OK)
        except Integration.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        try:
            integration = Integration.objects.get(pk=pk)

            # Delete associated webhooks
            for webhook in integration.webhook_set.all():
                if integration.service_type == 'github':
                    # Call GitHub API to delete webhook (mocked)
                    print(f"DELETING WEBHOOK {webhook.external_id} from GitHub")

            integration.delete()
            return Response({'status': 'Integration and associated webhooks deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Integration.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


# -------------------------
# Webhook ViewSet
# -------------------------
class WebhookViewSet(ViewSet):
    """Inspect Webhook records."""
    def list(self, request):
        webhooks = Webhook.objects.all()
        data = [w.to_dict() for w in webhooks]  # Ensure Webhook has to_dict
        return Response({'data': data}, status=status.HTTP_200_OK)


# -------------------------
# GitHub OAuth Callback
# -------------------------
class GitHubOAuthCallback(APIView):
    """Handles GitHub OAuth 2.0 flow."""

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        repo_owner = request.query_params.get('repo_owner')
        repo_name = request.query_params.get('repo_name')

        if not code or not state:
            return Response({'error': 'Missing code or state'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get or create integration instance for user
            integration, _ = Integration.objects.get_or_create(
                service_type='github', 
                user=request.user, 
                defaults={'name': f'{repo_owner}/{repo_name}'}
            )

            github_client = GitHubIntegration(integration)
            github_client.connect_repository(repo_owner, repo_name, code, request.build_absolute_uri())

            return Response({'status': 'GitHub integration successful!'}, status=status.HTTP_200_OK)

        except GitHubIntegrationError as e:
            logger.error(f"GitHub callback failure: {e}")
            return Response({'error': f'Integration failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# GitHub Webhook Receiver
# -------------------------
class GitHubWebhookReceiver(APIView):
    """Receives GitHub webhooks."""

    def post(self, request):
        signature = request.headers.get('X-Hub-Signature-256')
        event = request.headers.get('X-GitHub-Event')
        payload_body = request.body

        try:
            payload = json.loads(payload_body.decode('utf-8'))
        except json.JSONDecodeError:
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

        integration = Integration.objects.first()  # Replace with lookup logic by repo
        github_client = GitHubIntegration(integration)

        if not github_client.verify_webhook_signature(signature, payload_body):
            return Response({'error': 'Signature mismatch'}, status=status.HTTP_403_FORBIDDEN)

        if event == 'push':
            print(f"Processing PUSH event by {payload.get('sender', {}).get('login')}")
        elif event == 'issues':
            print(f"Processing ISSUES event: action={payload.get('action')}")

        return Response({'status': 'Payload processed successfully'}, status=status.HTTP_200_OK)


# -------------------------
# Slack Webhook Receiver
# -------------------------
class SlackWebhookReceiver(APIView):
    """Receives Slack commands and interactive payloads."""

    def post(self, request):
        try:
            payload = request.data

            if payload.get('command'):
                integration = Integration.objects.all()[1]  # Replace with proper user lookup
                slack_client = SlackIntegration(integration)
                response_text = slack_client.handle_slash_command(payload)
                return Response({'text': response_text}, status=status.HTTP_200_OK)

            elif payload.get('payload'):
                interactive_payload = json.loads(payload.get('payload'))
                print(f"Processing interactive action: {interactive_payload.get('callback_id')}")
                return Response({'status': 'Interactive payload received'}, status=status.HTTP_200_OK)

            return Response({'status': 'Unknown Slack request'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Slack webhook processing error: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
