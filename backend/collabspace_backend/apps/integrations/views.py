from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
import json
import logging

from .models import Integration, Webhook
from .serializers import IntegrationSerializer, WebhookSerializer
from .github import GitHubIntegration, GitHubIntegrationError
from .slack import SlackIntegration
from .jira import JiraIntegrationError

logger = logging.getLogger(__name__)


# -------------------------
# Integration ViewSet
# -------------------------
class IntegrationViewSet(viewsets.ModelViewSet):
    """
    CRUD operations on Integrations.
    
    Endpoints:
    - GET /api/integrations/integrations/ - List all user's integrations
    - POST /api/integrations/integrations/ - Create new integration
    - GET /api/integrations/integrations/{id}/ - Retrieve specific integration
    - PUT /api/integrations/integrations/{id}/ - Update integration
    - PATCH /api/integrations/integrations/{id}/ - Partial update
    - DELETE /api/integrations/integrations/{id}/ - Delete integration
    - POST /api/integrations/integrations/{id}/activate/ - Activate integration
    - POST /api/integrations/integrations/{id}/deactivate/ - Deactivate integration
    """
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return integrations for the current user only"""
        return Integration.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related('webhooks')
    
    def perform_create(self, serializer):
        """Automatically set the user when creating"""
        try:
            serializer.save(user=self.request.user)
            logger.info(
                f"Integration created by user {self.request.user.id}",
                extra={
                    'user_id': str(self.request.user.id),
                    'service_type': serializer.validated_data.get('service_type')
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to create integration: {str(e)}",
                exc_info=True,
                extra={'user_id': str(self.request.user.id)}
            )
            raise
    
    def destroy(self, request, *args, **kwargs):
        """Delete integration and associated webhooks"""
        try:
            integration = self.get_object()
            service_type = integration.service_type
            
            # Delete associated webhooks from external services
            webhook_count = 0
            for webhook in integration.webhooks.all():
                try:
                    if service_type == 'github':
                        logger.info(f"Deleting webhook {webhook.external_id} from GitHub")
                        # TODO: Call GitHub API to delete webhook
                        # github_client = GitHubIntegration(integration)
                        # github_client.delete_webhook(webhook.external_id)
                    elif service_type == 'slack':
                        logger.info(f"Deleting webhook {webhook.external_id} from Slack")
                        # TODO: Call Slack API to delete webhook
                    elif service_type == 'jira':
                        logger.info(f"Deleting webhook {webhook.external_id} from Jira")
                        # TODO: Call Jira API to delete webhook
                    
                    webhook_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to delete webhook {webhook.id}: {str(e)}",
                        exc_info=True
                    )
            
            integration_id = integration.id
            integration.delete()
            
            logger.info(
                f"Integration {integration_id} deleted with {webhook_count} webhooks",
                extra={
                    'integration_id': str(integration_id),
                    'webhook_count': webhook_count
                }
            )
            
            return Response(
                {
                    'status': 'success',
                    'message': f'Integration and {webhook_count} webhook(s) deleted'
                },
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            logger.error(f"Failed to delete integration: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to delete integration: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an integration"""
        integration = self.get_object()
        integration.is_active = True
        integration.save(update_fields=['is_active', 'updated_at'])
        
        logger.info(f"Integration {integration.id} activated")
        
        return Response(
            {'status': 'success', 'message': 'Integration activated'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an integration"""
        integration = self.get_object()
        integration.is_active = False
        integration.save(update_fields=['is_active', 'updated_at'])
        
        logger.info(f"Integration {integration.id} deactivated")
        
        return Response(
            {'status': 'success', 'message': 'Integration deactivated'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def webhooks(self, request, pk=None):
        """Get all webhooks for this integration"""
        integration = self.get_object()
        webhooks = integration.webhooks.all()
        serializer = WebhookSerializer(webhooks, many=True)
        
        return Response(
            {'data': serializer.data},
            status=status.HTTP_200_OK
        )


# -------------------------
# Webhook ViewSet
# -------------------------
class WebhookViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only operations on Webhooks.
    
    Endpoints:
    - GET /api/integrations/webhooks/ - List all user's webhooks
    - GET /api/integrations/webhooks/{id}/ - Retrieve specific webhook
    """
    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return webhooks for integrations owned by current user"""
        return Webhook.objects.filter(
            integration__user=self.request.user
        ).select_related('integration')


# -------------------------
# GitHub OAuth Callback
# -------------------------
class GitHubOAuthCallback(APIView):
    """
    Handles GitHub OAuth 2.0 flow.
    
    Expected query parameters:
    - code: OAuth authorization code
    - state: State parameter for CSRF protection
    - repo_owner: GitHub repository owner
    - repo_name: GitHub repository name
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        repo_owner = request.query_params.get('repo_owner')
        repo_name = request.query_params.get('repo_name')

        # Validate required parameters
        if not code or not state:
            logger.warning("GitHub OAuth callback missing code or state")
            return Response(
                {'error': 'Missing code or state parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not repo_owner or not repo_name:
            logger.warning("GitHub OAuth callback missing repo info")
            return Response(
                {'error': 'Missing repo_owner or repo_name parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get or create integration instance for user
            integration, created = Integration.objects.get_or_create(
                service_type='github',
                user=request.user,
                name=f'{repo_owner}/{repo_name}',
                defaults={
                    'settings': {
                        'repo_owner': repo_owner,
                        'repo_name': repo_name
                    }
                }
            )
            
            if not created:
                # Update settings if integration already exists
                integration.settings.update({
                    'repo_owner': repo_owner,
                    'repo_name': repo_name
                })
                integration.save(update_fields=['settings', 'updated_at'])

            # Connect to GitHub repository
            github_client = GitHubIntegration(integration)
            github_client.connect_repository(
                repo_owner,
                repo_name,
                code,
                request.build_absolute_uri()
            )
            
            logger.info(
                f"GitHub integration successful for {repo_owner}/{repo_name}",
                extra={
                    'user_id': str(request.user.id),
                    'integration_id': str(integration.id)
                }
            )

            return Response(
                {
                    'status': 'success',
                    'message': 'GitHub integration successful!',
                    'integration_id': str(integration.id)
                },
                status=status.HTTP_200_OK
            )

        except GitHubIntegrationError as e:
            logger.error(
                f"GitHub callback failure: {str(e)}",
                exc_info=True,
                extra={'user_id': str(request.user.id)}
            )
            return Response(
                {'error': f'Integration failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in GitHub callback: {str(e)}",
                exc_info=True,
                extra={'user_id': str(request.user.id)}
            )
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------
# GitHub Webhook Receiver
# -------------------------
class GitHubWebhookReceiver(APIView):
    """
    Receives and processes GitHub webhooks.
    
    This endpoint should be registered as a webhook URL in GitHub repository settings.
    GitHub will send POST requests to this endpoint when events occur.
    """
    permission_classes = []  # Public endpoint (verified by signature)

    def post(self, request):
        signature = request.headers.get('X-Hub-Signature-256')
        event = request.headers.get('X-GitHub-Event')
        delivery_id = request.headers.get('X-GitHub-Delivery')
        payload_body = request.body

        # Validate signature presence
        if not signature:
            logger.warning("GitHub webhook received without signature")
            return Response(
                {'error': 'Missing signature'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Parse payload
        try:
            payload = json.loads(payload_body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {str(e)}")
            return Response(
                {'error': 'Invalid JSON payload'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find integration by repository
        repository = payload.get('repository', {})
        repo_full_name = repository.get('full_name')
        
        if not repo_full_name:
            logger.warning("GitHub webhook missing repository information")
            return Response(
                {'error': 'Missing repository information'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Find integration for this repository
            integration = Integration.objects.filter(
                service_type='github',
                name=repo_full_name,
                is_active=True
            ).first()
            
            if not integration:
                logger.warning(f"No active integration found for {repo_full_name}")
                return Response(
                    {'error': 'Integration not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verify webhook signature
            github_client = GitHubIntegration(integration)
            if not github_client.verify_webhook_signature(signature, payload_body):
                logger.warning(
                    f"Signature verification failed for {repo_full_name}",
                    extra={'delivery_id': delivery_id}
                )
                return Response(
                    {'error': 'Signature verification failed'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Process event
            logger.info(
                f"Processing GitHub {event} event for {repo_full_name}",
                extra={
                    'event': event,
                    'delivery_id': delivery_id,
                    'integration_id': str(integration.id)
                }
            )

            # Handle different event types
            if event == 'push':
                self._handle_push_event(payload, integration)
            elif event == 'issues':
                self._handle_issues_event(payload, integration)
            elif event == 'pull_request':
                self._handle_pull_request_event(payload, integration)
            elif event == 'issue_comment':
                self._handle_comment_event(payload, integration)
            else:
                logger.info(f"Unhandled event type: {event}")

            return Response(
                {'status': 'success', 'message': 'Webhook processed'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Error processing GitHub webhook: {str(e)}",
                exc_info=True,
                extra={'delivery_id': delivery_id}
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _handle_push_event(self, payload, integration):
        """Handle push events"""
        sender = payload.get('sender', {}).get('login')
        commits = payload.get('commits', [])
        logger.info(f"Push by {sender}: {len(commits)} commit(s)")
        # TODO: Create notifications, update tasks, etc.

    def _handle_issues_event(self, payload, integration):
        """Handle issue events"""
        action = payload.get('action')
        issue = payload.get('issue', {})
        logger.info(f"Issue {action}: #{issue.get('number')}")
        # TODO: Create notifications, sync with internal tasks

    def _handle_pull_request_event(self, payload, integration):
        """Handle pull request events"""
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        logger.info(f"PR {action}: #{pr.get('number')}")
        # TODO: Create notifications, update code review tasks

    def _handle_comment_event(self, payload, integration):
        """Handle comment events"""
        action = payload.get('action')
        comment = payload.get('comment', {})
        logger.info(f"Comment {action}: {comment.get('id')}")
        # TODO: Create notifications for mentioned users


# -------------------------
# Slack Webhook Receiver
# -------------------------
class SlackWebhookReceiver(APIView):
    """
    Receives Slack slash commands and interactive payloads.
    
    This endpoint handles:
    - Slash commands (e.g., /task create)
    - Interactive components (buttons, modals)
    - Events API subscriptions
    """
    permission_classes = []  # Public endpoint (verified by Slack signing secret)

    def post(self, request):
        try:
            payload = request.data
            
            # Handle URL verification challenge (for Events API)
            if payload.get('type') == 'url_verification':
                return Response(
                    {'challenge': payload.get('challenge')},
                    status=status.HTTP_200_OK
                )

            # Handle slash commands
            if payload.get('command'):
                return self._handle_slash_command(payload)

            # Handle interactive payloads (buttons, modals, etc.)
            if payload.get('payload'):
                return self._handle_interactive_payload(payload)

            # Handle Events API callbacks
            if payload.get('event'):
                return self._handle_event(payload)

            logger.warning("Unknown Slack request type")
            return Response(
                {'status': 'Unknown request type'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Slack webhook processing error: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _handle_slash_command(self, payload):
        """Handle Slack slash commands"""
        command = payload.get('command')
        user_id = payload.get('user_id')
        team_id = payload.get('team_id')
        
        logger.info(f"Slash command {command} from {user_id}")
        
        try:
            # Find integration for this Slack workspace
            integration = Integration.objects.filter(
                service_type='slack',
                settings__team_id=team_id,
                is_active=True
            ).first()
            
            if not integration:
                return Response(
                    {'text': 'Integration not found. Please reconnect.'},
                    status=status.HTTP_200_OK
                )
            
            slack_client = SlackIntegration(integration)
            response_text = slack_client.handle_slash_command(payload)
            
            return Response(
                {'text': response_text},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error handling slash command: {str(e)}", exc_info=True)
            return Response(
                {'text': 'An error occurred processing your command.'},
                status=status.HTTP_200_OK
            )

    def _handle_interactive_payload(self, payload):
        """Handle Slack interactive components"""
        try:
            interactive_payload = json.loads(payload.get('payload'))
            callback_id = interactive_payload.get('callback_id')
            user = interactive_payload.get('user', {})
            
            logger.info(
                f"Interactive payload: {callback_id} from {user.get('id')}"
            )
            
            # TODO: Handle different callback IDs
            # Example: task approval, button clicks, modal submissions
            
            return Response(
                {'status': 'success'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(
                f"Error handling interactive payload: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _handle_event(self, payload):
        """Handle Slack Events API callbacks"""
        event = payload.get('event', {})
        event_type = event.get('type')
        
        logger.info(f"Slack event: {event_type}")
        
        # TODO: Handle different event types
        # Examples: message.channels, app_mention, reaction_added
        
        return Response(status=status.HTTP_200_OK)