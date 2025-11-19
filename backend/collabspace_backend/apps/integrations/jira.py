from .models import Integration
from typing import Dict, Any
import base64

class HTTP:
    """Mock HTTP client for external API calls."""
    def get(self, url, headers=None):
        print(f"MOCK JIRA API CALL: GET {url}")
        return type('Response', (object,), {'status_code': 200, 'json': lambda: {'issues': [{'key': 'PRO-1', 'summary': 'Mock issue'}]}})()
    
    def post(self, url, json=None, headers=None):
        print(f"MOCK JIRA API CALL: POST {url}")
        return type('Response', (object,), {'status_code': 201, 'json': lambda: {'key': 'PRO-999', 'id': '999'}})()

http_client = HTTP()


class JiraIntegrationError(Exception):
    """Custom error for Jira API failures."""
    pass


class JiraIntegration:
    """
    Handles all Jira-specific API interactions, typically using Basic Auth 
    (email/API Token) or OAuth for better security.
    """
    def __init__(self, integration_instance: Integration):
        self.integration = integration_instance
        # Assuming username/email and API token are stored in Integration.settings
        self.username = self.integration.settings.get('jira_username')
        self.api_token = self.integration.access_token 
        self.base_url = self.integration.settings.get('jira_url') # e.g., 'https://your-domain.atlassian.net'
        
    def _get_headers(self):
        """Uses Basic Auth: base64(username:token)"""
        if not self.username or not self.api_token:
            raise JiraIntegrationError("Jira credentials not configured.")

        credentials = f"{self.username}:{self.api_token}".encode('ascii')
        auth_header = base64.b64encode(credentials).decode('ascii')
        
        return {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    
    def import_issues(self, project_key: str, max_results: int = 50):
        """
        Fetches issues from a specific Jira project using JQL.
        
        Implements error recovery by checking for 401/403 status codes.
        """
        jql_query = f'project = {project_key} ORDER BY created DESC'
        url = f'{self.base_url}/rest/api/3/search?jql={jql_query}&maxResults={max_results}'
        
        print(f"IMPORTING ISSUES for {project_key}...")
        try:
            response = http_client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                issues = response.json().get('issues', [])
                # Logic to parse and store issue data in our system
                return issues
            elif response.status_code in [401, 403]:
                # Error Recovery: Authentication failure
                self.integration.is_active = False
                self.integration.save()
                raise JiraIntegrationError("Jira authentication failed. Integration deactivated.")
            else:
                raise JiraIntegrationError(f"Failed to fetch issues. Status: {response.status_code}")

        except Exception as e:
            # Catches network errors, connection timeouts, etc.
            print(f"Critical Jira import failure: {e}")
            raise JiraIntegrationError(f"Failed to connect to Jira: {e}")


    def sync_task_status(self, issue_key: str, new_status: str):
        """
        Updates the status/transition of a task in Jira.
        """
        # 1. Find the appropriate transition ID for the new status
        # This requires an initial call to /rest/api/3/issue/{issueKey}/transitions
        
        # 2. Execute the transition
        url = f'{self.base_url}/rest/api/3/issue/{issue_key}/transitions'
        transition_payload = {
            "transition": {
                "id": "21" # Mock Transition ID for 'To Do' -> 'In Progress'
            }
        }
        
        print(f"SYNCING TASK STATUS for {issue_key} to {new_status}...")
        try:
            response = http_client.post(url, json=transition_payload, headers=self._get_headers())
            
            if response.status_code == 204: # No Content on successful transition
                print(f"Successfully transitioned {issue_key}")
                return True
            else:
                # Error: Log detailed response to aid recovery
                print(f"Jira status update failed for {issue_key}. Response: {response.status_code}")
                raise JiraIntegrationError(f"Task transition failed: {response.status_code}")
        
        except Exception as e:
            raise JiraIntegrationError(f"Jira sync failed: {e}")