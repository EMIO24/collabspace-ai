# apps/messaging/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, MessageReaction
from apps.notifications.models import Notification


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """Create notification when a new message is sent"""
    if created:
        from .models import ChannelMember
        
        members = ChannelMember.objects.filter(
            channel=instance.channel
        ).exclude(user=instance.sender)
        
        for member in members:
            Notification.objects.create(
                user=member.user,
                type='message',  # Correct field name
                title=f'New message in #{instance.channel.name}',
                message=f'{instance.sender.username}: {instance.content[:50]}...',
                priority='medium',
                related_object_type='message',
                related_object_id=instance.id,
            )


@receiver(post_save, sender=MessageReaction)
def create_reaction_notification(sender, instance, created, **kwargs):
    """Create notification when someone reacts to a message"""
    if created and instance.message.sender != instance.user:
        Notification.objects.create(
            user=instance.message.sender,
            type='comment',  # Using 'comment' as reaction type
            title='New Reaction',
            message=f'{instance.user.username} reacted {instance.emoji} to your message',
            priority='low',
            related_object_type='message',
            related_object_id=instance.message.id,
        )