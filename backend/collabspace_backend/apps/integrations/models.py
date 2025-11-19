# apps/integrations/models.py

# --- Mock Framework Imports & Classes ---
# In a real framework (e.g., Django), these would be imported 
# from 'django.db.models', but are defined here for the mock setup.

class Model:
    """Mock base class for database models."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    @staticmethod
    def objects():
        # A mock manager that simulates basic ORM operations
        return type('MockManager', (object,), {
            'all': lambda: [], 
            'get': lambda **kwargs: None,
            'save': lambda: print("Mock Model saved."),
            'delete': lambda: print("Mock Model deleted.")
        })()
    
    def save(self):
        print(f"Saving mock instance of {self.__class__.__name__}")
        Model.objects().save()

    def delete(self):
        print(f"Deleting mock instance of {self.__class__.__name__}")
        Model.objects().delete()


# Mock Field Definitions
class JSONField(object):
    """Mock JSON field for settings."""
    def __init__(self, default=None):
        pass

class ForeignKey(object):
    """Mock ForeignKey."""
    def __init__(self, to, on_delete):
        pass

class DateTimeField(object):
    """Mock DateTimeField."""
    def __init__(self, auto_now_add=False, null=False, blank=False):
        pass

class CharField(object):
    """Mock CharField."""
    def __init__(self, max_length, null=False, blank=False, choices=None):
        pass

class TextField(object):
    """Mock TextField."""
    def __init__(self, null=False, blank=False):
        pass

class BooleanField(object):
    """Mock BooleanField."""
    def __init__(self, default=False):
        pass

# --- Core Integration Models ---

class Integration(Model):
    """
    Stores connection details, credentials, and settings for third-party services.
    
    Represents an active connection (e.g., a specific GitHub repository connection 
    or a Slack workspace connection).
    """
    SERVICE_CHOICES = (
        ('github', 'GitHub'),
        ('slack', 'Slack'),
        ('jira', 'Jira'),
    )

    # General Integration Fields
    user = ForeignKey('User', on_delete='CASCADE') # Link to the user who created the integration
    service_type = CharField(max_length=50, choices=SERVICE_CHOICES)
    name = CharField(max_length=255)
    
    # OAuth/Credentials Storage
    client_id = CharField(max_length=255, null=True, blank=True)
    access_token = TextField(null=True, blank=True)
    refresh_token = TextField(null=True, blank=True)
    token_expiry = DateTimeField(null=True, blank=True)
    
    # Service-Specific Configuration (e.g., repo_name, workspace_id, jira_url)
    settings = JSONField(default=dict) 
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.service_type} Integration for {self.user}'


class Webhook(Model):
    """
    Stores details about webhooks registered with the third-party service.
    
    This is necessary to track and manage webhooks (e.g., deleting them upon
    integration deactivation).
    """
    integration = ForeignKey(Integration, on_delete='CASCADE')
    service_event = CharField(max_length=100) # e.g., 'push', 'issue_comment', 'pull_request'
    external_id = CharField(max_length=255) # The ID assigned by GitHub/Jira/Slack
    target_url = TextField() # The full URL of our receiver endpoint
    secret = CharField(max_length=255) # The secret used to verify payloads

    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Webhook for {self.integration.service_type} on {self.service_event}'