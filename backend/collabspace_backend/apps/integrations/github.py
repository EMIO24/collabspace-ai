import json
import hmac
import hashlib

# Mock classes for models and HTTP requests
from .models import Integration, Webhook
from typing import Dict, Any

class HTTP:
    """Mock HTTP client for external API calls."""
    def get(self, url, headers=None):
        print(f"MOCK API CALL: GET {url}")
        return type('Response', (object,), {'status_code': 200, 'json': lambda: {'data': 'mock_data'}})()
    
    def post(self, url, json=None, headers=None):
        print(f"MOCK API CALL: POST {url}")
        return type('Response', (object,), {'status_code': 201, 'json': lambda: {'id': 'wh_123', 'url': 'mock_url'}})()
    
    def delete(self, url, headers=None):
        print(f"MOCK API CALL: DELETE {url}")
        return type('Response', (object,), {'status_code': 204})()

http_client = HTTP()


class GitHubIntegrationError(Exception):
    """Custom error for GitHub API failures."""
    pass


class BaseIntegration:
    """Base class for all integrations to handle common logic."""
    def __init__(self, integration_instance: Integration):
        self.integration = integration_instance
        self.access_token = integration_instance.access_token
        self.base_url = "https://api.github.com"
    
    def _get_headers(self):
        return {
            'Authorization': f'token {self.access_token}',
            'Accept': 'application/vnd.github.v3+json',
        }


class GitHubIntegration(BaseIntegration):
    """
    Handles all GitHub-specific API interactions, including OAuth, 
    webhook registration, and data synchronization.
    """
    def __init__(self, integration_instance: Integration):
        super().__init__(integration_instance)
        # Assuming the Integration.settings contains 'repo_owner' and 'repo_name'
        self.repo_owner = self.integration.settings.get('repo_owner')
        self.repo_name = self.integration.settings.get('repo_name')
        self.repo_full_name = f"{self.repo_owner}/{self.repo_name}"


    def connect_repository(self, owner: str, name: str, oauth_code: str, redirect_uri: str) -> bool:
        """
        Completes the OAuth flow to get an access token and sets up the integration.
        
        This is typically called right after the user returns from GitHub's authorization page.
        """
        # 1. Exchange OAuth code for access token
        # This requires the client_secret (stored securely outside the model, e.g., in environment vars)
        try:
            # Mock exchange for token
            print(f"EXCHANGING CODE {oauth_code} FOR TOKEN...")
            self.integration.access_token = "gho_mock_token"
            self.integration.settings['repo_owner'] = owner
            self.integration.settings['repo_name'] = name
            self.integration.save() # Mock save
            
            # 2. Register webhooks for required events
            self.register_webhooks(['push', 'issues', 'pull_request'])
            return True
        except Exception as e:
            print(f"GitHub connection failed: {e}")
            raise GitHubIntegrationError(f"OAuth failed: {e}")

    
    def register_webhooks(self, events: list, webhook_receiver_url: str = 'https://our-api.com/webhooks/github/'):
        """Registers a set of events as webhooks on the configured repository."""
        webhook_secret = 'super_secret_key_from_env' # Should be securely generated
        
        config = {
            "url": webhook_receiver_url,
            "content_type": "json",
            "secret": webhook_secret,
            "insecure_ssl": "0"
        }
        
        payload = {
            "name": "web",
            "active": True,
            "events": events,
            "config": config
        }
        
        url = f'{self.base_url}/repos/{self.repo_full_name}/hooks'
        
        try:
            response = http_client.post(url, json=payload, headers=self._get_headers())
            if response.status_code == 201:
                response_data = response.json()
                # Create a Webhook model instance to track the registration
                Webhook(
                    integration=self.integration,
                    service_event=','.join(events),
                    external_id=response_data.get('id'),
                    target_url=webhook_receiver_url,
                    secret=webhook_secret,
                ).save() # Mock save
                print("Webhooks registered successfully.")
            else:
                raise GitHubIntegrationError(f"Failed to register webhook. Status: {response.status_code}")
        except Exception as e:
            raise GitHubIntegrationError(f"Webhook registration error: {e}")


    def sync_commits(self):
        """Fetches and stores recent commits."""
        print(f"SYNCING COMMITS for {self.repo_full_name}...")
        url = f'{self.base_url}/repos/{self.repo_full_name}/commits'
        try:
            response = http_client.get(url, headers=self._get_headers())
            # Logic to parse and store commit data...
            return response.json().get('data')
        except Exception as e:
            raise GitHubIntegrationError(f"Commit sync failed: {e}")

    # sync_prs and sync_issues would follow a similar pattern, querying different endpoints

    def verify_webhook_signature(self, signature: str, payload_body: bytes) -> bool:
        """
        Verifies the signature of the incoming webhook payload using the stored secret.
        
        This is a critical security step for all incoming webhooks.
        """
        # The secret must be retrieved from the Webhook model instance
        webhook_secret = self.integration.webhook_set.all()[0].secret # Mock retrieval
        
        if not signature:
            return False

        sha_name, signature_hash = signature.split('=')
        if sha_name != 'sha256': # GitHub sometimes uses sha1, but sha256 is better
            return False
            
        # Create HMAC digest
        mac = hmac.new(webhook_secret.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = mac.hexdigest()
        
        # Constant time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature_hash)

    # --- Error Recovery ---
    def check_token_status(self):
        """Checks if the access token is still valid (e.g., via a /user call)."""
        print("Checking GitHub token validity...")
        url = f'{self.base_url}/user'
        response = http_client.get(url, headers=self._get_headers())
        if response.status_code in [401, 403]:
            self.integration.is_active = False
            self.integration.save()
            print("Token expired or revoked. Integration marked inactive.")
            return False
        return True