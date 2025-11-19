from .models import Integration
from typing import Dict, Any

class HTTP:
    """Mock HTTP client for external API calls."""
    def post(self, url, json=None, headers=None):
        print(f"MOCK SLACK API CALL: POST {url}")
        return type('Response', (object,), {'status_code': 200, 'json': lambda: {'ok': True}})()

http_client = HTTP()


class SlackIntegrationError(Exception):
    """Custom error for Slack API failures."""
    pass


class SlackIntegration:
    """
    Handles all Slack-specific API interactions for notifications and commands.
    """
    def __init__(self, integration_instance: Integration):
        self.integration = integration_instance
        self.access_token = integration_instance.access_token
        self.base_url = "https://slack.com/api"
        # The OAuth scope usually grants the token
        
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json; charset=utf-8',
        }

    def send_notification(self, channel_id: str, message_text: str, blocks: list = None):
        """
        Sends a message to a specific Slack channel.
        """
        url = f'{self.base_url}/chat.postMessage'
        payload = {
            'channel': channel_id,
            'text': message_text,
            'blocks': blocks or []
        }
        
        try:
            response = http_client.post(url, json=payload, headers=self._get_headers())
            response_data = response.json()
            if not response_data.get('ok'):
                raise SlackIntegrationError(f"Slack message failed: {response_data.get('error')}")
            print(f"Message sent to channel {channel_id}.")
        except Exception as e:
            # Error recovery: Log the failed message and potentially retry later
            print(f"Error sending Slack notification: {e}")
            raise SlackIntegrationError(f"Notification failed: {e}")


    def handle_slash_command(self, payload: Dict[str, Any]) -> str:
        """
        Processes an incoming slash command payload from Slack.
        
        Payload verification (using request signing) is typically done in the view, 
        but the logic for command execution is here.
        """
        command = payload.get('command')
        text = payload.get('text', '').strip()
        user_id = payload.get('user_id')
        response_url = payload.get('response_url') # Used for delayed responses
        
        if command == '/status':
            if not text:
                response_message = "Please specify a project, e.g., `/status project-x`"
            else:
                # Mock logic to fetch status based on project name (text)
                response_message = f"Status for *{text}*: All systems nominal. (Fetched by user {user_id})"
                # A separate, delayed HTTP POST response could be sent to response_url here
                
        elif command == '/create-task':
            # Mock logic to parse the text and create a task in our system
            response_message = f"Task created: '{text}'."
        
        else:
            response_message = "Unknown command."

        return response_message