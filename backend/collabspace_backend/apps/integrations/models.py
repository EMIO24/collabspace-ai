# apps/integrations/models.py
import uuid
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Integration(BaseModel):
    """
    Stores connection details, credentials, and settings for third-party services.
    
    Represents an active connection (e.g., a specific GitHub repository connection 
    or a Slack workspace connection).
    """
    SERVICE_CHOICES = [
        ('github', 'GitHub'),
        ('slack', 'Slack'),
        ('jira', 'Jira'),
    ]

    # General Integration Fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='integrations'
    )
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    name = models.CharField(max_length=255)
    
    # OAuth/Credentials Storage
    client_id = models.CharField(max_length=255, null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    
    # Service-Specific Configuration (e.g., repo_name, workspace_id, jira_url)
    settings = models.JSONField(default=dict) 
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'integrations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'service_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.service_type} Integration for {self.user.username}'
    
    def to_dict(self):
        """Serialize integration to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user.id),
            'service_type': self.service_type,
            'name': self.name,
            'is_active': self.is_active,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Webhook(BaseModel):
    """
    Stores details about webhooks registered with the third-party service.
    
    This is necessary to track and manage webhooks (e.g., deleting them upon
    integration deactivation).
    """
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    service_event = models.CharField(max_length=100)
    # e.g., 'push', 'issue_comment', 'pull_request'
    
    external_id = models.CharField(max_length=255)
    # The ID assigned by GitHub/Jira/Slack
    
    target_url = models.TextField()
    # The full URL of our receiver endpoint
    
    secret = models.CharField(max_length=255)
    # The secret used to verify payloads

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['integration', 'service_event']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'Webhook for {self.integration.service_type} on {self.service_event}'
    
    def to_dict(self):
        """Serialize webhook to dictionary"""
        return {
            'id': str(self.id),
            'integration_id': str(self.integration.id),
            'service_event': self.service_event,
            'external_id': self.external_id,
            'target_url': self.target_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }