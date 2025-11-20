from django.db import models
from django.db.models import F, Q, Count
from django.utils import timezone
from apps.authentication.models import User # Assuming User model location
from apps.workspaces.models import Workspace # Assuming Workspace model location
from apps.core.models import BaseModel, TimeStampedModel



class Channel(BaseModel):
    """Chat channel/room"""
    CHANNEL_TYPES = (
        ('public', 'Public'),
        ('private', 'Private'),
        ('direct', 'Direct Message'),
    )
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    channel_type = models.CharField(max_length=10, choices=CHANNEL_TYPES, default='public')
    members = models.ManyToManyField(User, through='ChannelMember', related_name='channels')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_channels')
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.workspace.name})"

    def add_member(self, user, role='member'):
        """Adds a user to the channel."""
        member, created = ChannelMember.objects.get_or_create(
            channel=self,
            user=user,
            defaults={'role': role}
        )
        return member, created

    def remove_member(self, user):
        """Removes a user from the channel."""
        return ChannelMember.objects.filter(channel=self, user=user).delete()

    def archive(self):
        """Archives the channel."""
        self.is_archived = True
        self.save()


class ChannelMember(TimeStampedModel):
    """Channel membership"""
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    last_read_at = models.DateTimeField(null=True)
    notifications_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ['channel', 'user']
        verbose_name = 'Channel Member'

    def mark_as_read(self):
        """Updates last_read_at to the current time."""
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])

    def get_unread_count(self):
        """Returns the number of unread messages."""
        # Find the last message in the channel created before last_read_at
        if self.last_read_at:
            return self.channel.messages.filter(
                created_at__gt=self.last_read_at
            ).count()
        return self.channel.messages.count()


class Message(BaseModel):
    """Chat message"""
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('file', 'File'),
        ('system', 'System'),
    )

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')  # for threads
    mentions = models.ManyToManyField(User, related_name='mentioned_in_messages', blank=True)
    attachments = models.JSONField(default=list)  # list of Cloudinary URLs
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    is_deleted = models.BooleanField(default=False) # Soft delete

    class Meta:
        ordering = ['created_at']

    def add_attachment(self, file_url):
        """Adds a file URL to the attachments list."""
        if isinstance(self.attachments, list):
            self.attachments.append(file_url)
        else:
            self.attachments = [file_url] # Handle case where it might be null/None
        self.save(update_fields=['attachments'])

    def edit(self, new_content):
        """Edits the message content."""
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=['content', 'is_edited', 'edited_at'])

    def delete_soft(self):
        """Soft deletes the message."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])


class MessageReaction(TimeStampedModel):
    """Message emoji reactions"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)

    class Meta:
        unique_together = ['message', 'user', 'emoji']


class DirectMessage(BaseModel):
    """Direct message between two users"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    content = models.TextField()
    attachments = models.JSONField(default=list)  # Cloudinary URLs
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Ensures that a DM can be found regardless of sender/recipient order
        ordering = ['created_at']

    def mark_as_read(self):
        """Marks the direct message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])