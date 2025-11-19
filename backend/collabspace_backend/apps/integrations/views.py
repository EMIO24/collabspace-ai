from .models import Integration, Webhook
from .github import GitHubIntegration, GitHubIntegrationError
from .slack import SlackIntegration
from .jira import JiraIntegrationError
import json
import logging

logger = logging.getLogger(__name__)

# --- Mock Framework Classes (Django/DRF) ---
class ViewSet:
    """Mock DRF ViewSet for CRUD operations."""
    def list(self, request):
        return {'integrations': Integration.objects().all()}
    
    def create(self, request):
        # Basic create logic, token exchange happens in the callback
        return {'status': 'Integration entry created'}

class APIView:
    """Mock DRF APIView for standalone endpoints."""
    def get(self, request):
        return {'status': 'OK'}
    
    def post(self, request):
        return {'status': 'OK'}

# --- Integration and Webhook Management ---

class IntegrationViewSet(ViewSet):
    """API endpoint for CRUD operations on Integrations."""
    def list(self, request):
        """List all active and inactive integrations for the user."""
        return {'data': Integration.objects().all()} # Mock data retrieval

    def retrieve(self, request, pk):
        """Get details for a single integration."""
        try:
            integration = Integration.objects().get(pk=pk)
            return {'data': integration.__dict__}
        except:
            return {'error': 'Not found'}, 404

    # The actual token creation happens in the OAuth callback, not standard POST
    def destroy(self, request, pk):
        """Deactivate or delete an integration (including removing webhooks)."""
        try:
            integration = Integration.objects().get(pk=pk)
            # Webhook cleanup: Iterate through all webhooks and call the third-party API DELETE endpoint
            for webhook in integration.webhook_set.all():
                # Example: GitHub webhook deletion logic
                if integration.service_type == 'github':
                    # Mock delete call using webhook.external_id
                    print(f"DELETING WEBHOOK {webhook.external_id} from GitHub")
            
            # Delete local records
            integration.delete() # Mock delete
            return {'status': 'Integration and associated webhooks deleted'}, 204
        except:
            return {'error': 'Not found'}, 404


class WebhookViewSet(ViewSet):
    """API endpoint for inspecting Webhook records."""
    def list(self, request):
        return {'data': Webhook.objects().all()} # Mock data retrieval


# --- OAuth Callbacks ---

class GitHubOAuthCallback(APIView):
    """Handles the final step of the GitHub OAuth 2.0 flow."""
    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        repo_owner = request.query_params.get('repo_owner') # Passed via state or query params
        repo_name = request.query_params.get('repo_name') # Passed via state or query params

        if not code or not state:
            return {'error': 'Missing code or state in callback'}, 400
        
        # 1. State validation (CSRF protection) would go here
        # if not self._validate_state(state): return 403

        # 2. Exchange code for token and set up webhooks
        try:
            # Assume we have a placeholder integration instance linked to the user
            # This instance would be created before redirecting to GitHub
            mock_integration = Integration(service_type='github', user='current_user', name=f'{repo_owner}/{repo_name}')
            
            github_client = GitHubIntegration(mock_integration)
            github_client.connect_repository(repo_owner, repo_name, code, request.build_absolute_uri())
            
            return {'status': 'GitHub integration successful!'}, 200
        
        except GitHubIntegrationError as e:
            logger.error(f"GitHub callback failure: {e}")
            return {'error': f'Integration failed: {str(e)}'}, 500


# --- Webhook Receivers ---

class GitHubWebhookReceiver(APIView):
    """Receives and processes incoming GitHub webhook payloads."""
    def post(self, request):
        signature = request.headers.get('X-Hub-Signature-256')
        event = request.headers.get('X-GitHub-Event')
        payload_body = request.body # Raw bytes of the payload
        
        try:
            payload = json.loads(payload_body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload.")
            return {'error': 'Invalid payload'}, 400

        # 1. Security check: Verify the signature
        # We need the Webhook secret, which means we need to identify the webhook/repo.
        # This is often done by looking up the repository ID or another unique identifier in the payload.
        
        # Mock lookup: Assume we can find the correct Integration instance
        mock_integration = Integration.objects().all()[0] # In reality: query by payload data
        github_client = GitHubIntegration(mock_integration)
        
        if not github_client.verify_webhook_signature(signature, payload_body):
            logger.warning("Webhook signature verification failed.")
            return {'error': 'Signature mismatch'}, 403

        # 2. Process the event
        if event == 'push':
            # Logic to process new commits from the push event
            print(f"Processing PUSH event by {payload.get('sender', {}).get('login')}")
        elif event == 'issues':
            # Logic to update/create local issues
            print(f"Processing ISSUES event: action={payload.get('action')}")
        
        return {'status': 'Payload processed successfully'}, 200


class SlackWebhookReceiver(APIView):
    """Receives and processes incoming Slack slash commands and interactive payloads."""
    def post(self, request):
        # Slack uses request signing (X-Slack-Signature and X-Slack-Request-Timestamp) for verification.
        # This check should be performed here before any processing.
        
        # Assume verification passes (Error Recovery: 403 if check fails)
        
        try:
            # Slack command payloads are typically x-www-form-urlencoded
            payload = request.data # Mock access to form data
            
            if payload.get('command'):
                # Handle Slash Commands
                # Mock lookup for integration
                mock_integration = Integration.objects().all()[1] 
                slack_client = SlackIntegration(mock_integration)
                
                response_text = slack_client.handle_slash_command(payload)
                # For immediate responses, return text directly
                return {'text': response_text}, 200
            
            elif payload.get('payload'):
                # Handle Interactive components (buttons, menus)
                interactive_payload = json.loads(payload.get('payload'))
                print(f"Processing interactive action: {interactive_payload.get('callback_id')}")
                # Logic to handle the interactive component action
                return {'status': 'Interactive payload received'}, 200
            
            return {'status': 'Unknown Slack request'}, 200
        
        except Exception as e:
            logger.error(f"Slack webhook processing error: {e}")
            return {'error': 'Internal server error'}, 500