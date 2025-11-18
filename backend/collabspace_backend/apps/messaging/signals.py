from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

# Import necessary models (assuming they are defined in .models)
from .models import Message, DirectMessage, ChannelMember 

# Get the channel layer instance
channel_layer = get_channel_layer()

# --- Signal for Channel Messages (Message model) ---

@receiver(post_save, sender=Message)
def send_message_notifications(sender, instance, created, **kwargs):
    """
    Triggers real-time notification events when a new Message is created in a Channel.
    - Sends specific 'mention' notifications to mentioned users.
    - Sends general 'unread increment' notifications to other channel members.
    """
    if not created or not channel_layer:
        return

    message = instance
    channel_id = str(message.channel_id)
    sender_id = str(message.sender_id)

    # 1. Handle Mentions: Send a specific notification to mentioned users
    if message.mentions.exists():
        # Get IDs of mentioned users who are NOT the sender
        mentioned_user_ids = [
            str(uid) for uid in message.mentions
            .exclude(id=message.sender_id)
            .values_list('id', flat=True)
        ]
        
        mention_payload = {
            'type': 'notification.mention',
            'message_id': str(message.id),
            'channel_id': channel_id,
            'sender_id': sender_id,
            'content_preview': message.content[:50],
        }
        
        for user_id in mentioned_user_ids:
            # Send notification to the mentioned user's specific group ('user_<UUID>')
            async_to_sync(channel_layer.group_send)(
                f'user_{user_id}',
                mention_payload
            )

    # 2. Update Unread Counts: Notify other active members of the channel to update their UI/badge counts
    # NOTE: Fetching all members synchronously is a common performance risk. 
    # This is simplified here; in production, this would be optimized or delegated to an async task.
    member_ids_to_notify = ChannelMember.objects.filter(
        channel_id=channel_id,
        # Only notify users who have notifications enabled
        notifications_enabled=True 
    ).exclude(user_id=message.sender_id).values_list('user_id', flat=True)
    
    unread_payload = {
        'type': 'notification.unread_increment',
        'channel_id': channel_id,
    }

    for member_id in member_ids_to_notify:
        # Send a general unread count signal to each member's user group
        async_to_sync(channel_layer.group_send)(
            f'user_{str(member_id)}',
            unread_payload
        )


# --- Signal for Direct Messages (DirectMessage model) ---

@receiver(post_save, sender=DirectMessage)
def send_dm_notification(sender, instance, created, **kwargs):
    """Notify recipient of a new Direct Message (DM) via the channel layer."""
    if not created or not channel_layer:
        return

    dm = instance
    recipient_id = str(dm.recipient_id)
    
    # Send a notification event to the recipient's user group
    async_to_sync(channel_layer.group_send)(
        f'user_{recipient_id}',
        {
            'type': 'notification.dm_received',
            'dm_id': str(dm.id),
            'sender_id': str(dm.sender_id),
            'content_preview': dm.content[:50],
        }
    )