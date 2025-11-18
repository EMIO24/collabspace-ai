import uuid
from django.db import models
from apps.core.models import BaseModel
from django.utils import timezone
from datetime import time as dt_time

class Notification(BaseModel):
    """In-app notification"""
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, db_index=True)
    # Types: task_assigned, mention, comment, deadline, project_invite, workspace_invite
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.URLField(null=True, blank=True)
    
    # Generic relation
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    related_object_id = models.UUIDField(null=True, blank=True)
    
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    PRIORITY_CHOICES = [
        ('low', 'Low'), 
        ('medium', 'Medium'), 
        ('high', 'High')
    ]
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'type']),
        ]
    
    def __str__(self):
        return f"{self.type} notification for {self.user.username}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField('authentication.User', on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    
    # Email frequency
    FREQUENCY_CHOICES = [
        ('instant', 'Instant'),
        ('daily_digest', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('never', 'Never')
    ]
    email_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='instant'
    )
    
    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Event preferences (JSONField)
    preferences = models.JSONField(default=dict)
    # Structure: {"task_assigned": {"email": true, "push": true}, ...}
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def get_preference(self, notification_type, channel):
        """Get preference for specific notification type and channel"""
        # Ensure preference key exists and channel is in the sub-dict, otherwise default to True
        if notification_type in self.preferences and isinstance(self.preferences[notification_type], dict):
            return self.preferences[notification_type].get(channel, True)
        return True  # Default to enabled
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours (considering timezone.now().time())"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        # Get the current time in the system's timezone (or preferred timezone)
        now = timezone.localtime(timezone.now()).time()

        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        # Case 1: Start <= End (Quiet hours within the same day)
        if start <= end:
            return start <= now <= end
        # Case 2: Start > End (Quiet hours cross midnight)
        else:
            return now >= start or now <= end