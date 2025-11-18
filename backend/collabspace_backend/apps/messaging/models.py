from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import uuid

# Get the User model defined in settings
User = settings.AUTH_USER_MODEL

# --- Base Models (Assumed Utilities) ---

class TimeStampedModel(models.Model):
    """Abstract base class providing creation and modification timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class BaseModel(TimeStampedModel):
    """Abstract base class providing a UUID primary key and timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

# --- Placeholder Models (Assumed from other apps) ---

class Workspace(BaseModel):
    """Placeholder for the Workspace model, needed for Channel FK."""
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_workspaces')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Workspace")
        verbose_name_plural = _("Workspaces")

# --- Messaging Models ---

class Channel(BaseModel):
    """Chat channel/room within a workspace."""
    CHANNEL_TYPES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    channel_type = models.CharField(max_length=10, choices=CHANNEL_TYPES, default='public')
    
    # Use ChannelMember as the through model for membership
    members = models.ManyToManyField(User, through='ChannelMember', related_name='chat_channels')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_channels')
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ('workspace', 'name')
        ordering = ['name']
        verbose_name = _("Channel")
        verbose_name_plural = _("Channels")

    def __str__(self):
        return f"[{self.workspace.name}] #{self.name}"

class ChannelMember(TimeStampedModel):
    """Through model for Channel membership, tracking specific user settings."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    last_read_at = models.DateTimeField(null=True, blank=True)
    notifications_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('channel', 'user')
        verbose_name = _("Channel Member")
        verbose_name_plural = _("Channel Members")

    def __str__(self):
        return f"{self.user.username} in {self.channel.name}"

class Message(BaseModel):
    """Chat message sent in a Channel."""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File/Attachment'),
        ('system', 'System Message'),
    ]
    
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    
    # For threading (replying to a specific message)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies') 
    
    mentions = models.ManyToManyField(User, related_name='mentioned_in_messages', blank=True)
    
    # List of file URLs or references
    attachments = models.JSONField(default=list, encoder=DjangoJSONEncoder, blank=True)
    
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    
    # Flexible storage for additional message details
    metadata = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True) 

    class Meta:
        ordering = ['created_at']
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

class MessageReaction(TimeStampedModel):
    """Message emoji reactions."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reactions')
    emoji = models.CharField(max_length=50)

    class Meta:
        unique_together = ('message', 'user', 'emoji')
        verbose_name = _("Message Reaction")
        verbose_name_plural = _("Message Reactions")

class DirectMessage(BaseModel):
    """Direct message between two users."""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _("Direct Message")
        verbose_name_plural = _("Direct Messages")