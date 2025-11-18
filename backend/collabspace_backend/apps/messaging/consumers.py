from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import json
import re
from django.utils import timezone
from apps.authentication.models import User
from .models import Channel, ChannelMember, Message, MessageReaction


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time messaging"""

    async def connect(self):
        """Handle WebSocket connection"""
        self.workspace_id = self.scope['url_route']['kwargs']['workspace_id']
        self.workspace_group_name = f'workspace_{self.workspace_id}'
        self.user = self.scope['user']

        # Verify user is authenticated and is a workspace member
        if not self.user.is_authenticated or not await self.is_workspace_member():
            await self.close(code=4001) # Unauthorized/Forbidden
            return

        # Join the global workspace group (for user status/global notifications)
        await self.channel_layer.group_add(
            self.workspace_group_name,
            self.channel_name
        )

        await self.accept()

        # Send online status to workspace room
        await self.channel_layer.group_send(
            self.workspace_group_name,
            {
                'type': 'user_online',
                'user_id': str(self.user.id),
                'username': self.user.username,
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.user.is_authenticated:
            # Send offline status to workspace room
            await self.channel_layer.group_send(
                self.workspace_group_name,
                {
                    'type': 'user_offline',
                    'user_id': str(self.user.id),
                }
            )

            # Leave the global workspace group
            await self.channel_layer.group_discard(
                self.workspace_group_name,
                self.channel_name
            )
        # Close connection if not already closed
        # The base consumer handles the close, this is for cleanup.

    async def receive_json(self, content):
        """Handle incoming JSON messages from WebSocket"""
        command = content.get('command')
        data = content.get('data', {})

        try:
            if not self.user.is_authenticated:
                await self.send_json({'type': 'error', 'message': 'Authentication required.'})
                return

            if command == 'join_channel':
                await self.handle_join_channel(data)
            elif command == 'leave_channel':
                await self.handle_leave_channel(data)
            elif command == 'new_message':
                await self.handle_new_message(data)
            elif command == 'typing_start':
                await self.handle_typing_start(data)
            elif command == 'typing_stop':
                await self.handle_typing_stop(data)
            elif command == 'message_read':
                await self.handle_message_read(data)
            elif command == 'message_edit':
                await self.handle_message_edit(data)
            elif command == 'message_delete':
                await self.handle_message_delete(data)
            elif command == 'reaction_add':
                await self.handle_reaction_add(data)
            elif command == 'reaction_remove':
                await self.handle_reaction_remove(data) # Added missing handler
            else:
                await self.send_json({'type': 'error', 'message': f'Unknown command: {command}'})

        except Channel.DoesNotExist:
            await self.send_json({'type': 'error', 'message': 'Channel not found.'})
        except Message.DoesNotExist:
            await self.send_json({'type': 'error', 'message': 'Message not found.'})
        except Exception as e:
            print(f"Error handling message: {e}")
            await self.send_json({'type': 'error', 'message': 'An internal error occurred.'})

    # --- Handlers for commands (sent FROM client) ---

    async def handle_join_channel(self, data):
        """Add consumer to channel group for message broadcasts."""
        channel_id = data.get('channel_id')
        if not await self.is_channel_member(channel_id):
            await self.send_json({'type': 'error', 'message': 'Not a member of this channel.'})
            return

        # Join the specific channel group
        self.channel_id = channel_id
        self.channel_group_name = f'channel_{channel_id}'
        await self.channel_layer.group_add(
            self.channel_group_name,
            self.channel_name
        )
        await self.send_json({'type': 'channel.joined', 'channel_id': channel_id})

    async def handle_leave_channel(self, data):
        """Remove consumer from channel group."""
        channel_id = data.get('channel_id')
        channel_group_name = f'channel_{channel_id}'
        await self.channel_layer.group_discard(
            channel_group_name,
            self.channel_name
        )
        await self.send_json({'type': 'channel.left', 'channel_id': channel_id})

    async def handle_new_message(self, data):
        """Save new message and broadcast it to the channel group"""
        channel_id = data.get('channel_id')
        content = data.get('content')
        parent_message_id = data.get('parent_message_id')
        attachments = data.get('attachments')

        if not content or not channel_id:
            await self.send_json({'type': 'error', 'message': 'Missing message content or channel ID.'})
            return

        if not await self.is_channel_member(channel_id):
            await self.send_json({'type': 'error', 'message': 'Not authorized to post to this channel.'})
            return

        message = await self.save_message(channel_id, content, parent_message_id, attachments)
        
        # Extract and save mentions (done asynchronously in the signal)

        serialized_message = await self.serialize_message(message)

        # Broadcast the new message to all channel members (including sender)
        await self.channel_layer.group_send(
            f'channel_{channel_id}',
            {
                'type': 'message_new', # Corresponds to the method below
                'message': serialized_message
            }
        )

        # Trigger message read update for sender (auto-read on send)
        await self.update_last_read(channel_id)


    async def handle_typing_start(self, data):
        """Start typing indicator"""
        channel_id = data.get('channel_id')

        await self.channel_layer.group_send(
            f'channel_{channel_id}',
            {
                'type': 'user_typing',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'channel_id': channel_id
            }
        )

    async def handle_typing_stop(self, data):
        """Stop typing indicator"""
        channel_id = data.get('channel_id')

        await self.channel_layer.group_send(
            f'channel_{channel_id}',
            {
                'type': 'user_stopped_typing',
                'user_id': str(self.user.id),
                'channel_id': channel_id
            }
        )

    async def handle_message_read(self, data):
        """Update last_read_at"""
        channel_id = data.get('channel_id')
        await self.update_last_read(channel_id)
        # No broadcast is usually needed for this

    async def handle_message_edit(self, data):
        """Edit message"""
        message_id = data.get('message_id')
        new_content = data.get('content')

        try:
            message = await self.edit_message(message_id, new_content)
        except Message.DoesNotExist:
            await self.send_json({'type': 'error', 'message': 'Message not found or not owned by user.'})
            return

        await self.channel_layer.group_send(
            f'channel_{message.channel_id}',
            {
                'type': 'message_updated',
                'message': await self.serialize_message(message)
            }
        )

    async def handle_message_delete(self, data):
        """Soft delete message"""
        message_id = data.get('message_id')

        try:
            channel_id = await self.delete_message(message_id) # Returns channel_id
        except Message.DoesNotExist:
            await self.send_json({'type': 'error', 'message': 'Message not found or not owned by user.'})
            return

        await self.channel_layer.group_send(
            f'channel_{channel_id}',
            {
                'type': 'message_deleted',
                'message_id': message_id
            }
        )

    async def handle_reaction_add(self, data):
        """Add reaction to message"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')

        reaction = await self.add_reaction(message_id, emoji)

        # Assuming reaction contains the message and user info
        message = await self.get_message(message_id)

        await self.channel_layer.group_send(
            f'channel_{message.channel_id}',
            {
                'type': 'reaction_added',
                'message_id': message_id,
                'emoji': emoji,
                'user_id': str(self.user.id)
            }
        )
    
    async def handle_reaction_remove(self, data):
        """Remove reaction from message (Missing handler in original prompt)"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')

        await self.remove_reaction(message_id, emoji)
        
        message = await self.get_message(message_id)

        await self.channel_layer.group_send(
            f'channel_{message.channel_id}',
            {
                'type': 'reaction_removed',
                'message_id': message_id,
                'emoji': emoji,
                'user_id': str(self.user.id)
            }
        )

    # --- Message types (sent TO client) ---

    async def message_new(self, event):
        """Send new message to client"""
        await self.send_json({
            'type': 'message.new',
            'message': event['message']
        })

    async def message_updated(self, event):
        """Send updated message to client"""
        await self.send_json({
            'type': 'message.updated',
            'message': event['message']
        })

    async def message_deleted(self, event):
        """Send deletion notification"""
        await self.send_json({
            'type': 'message.deleted',
            'message_id': event['message_id']
        })

    async def user_typing(self, event):
        """Send typing indicator"""
        # Don't send typing indicator back to the user who's typing
        if event['user_id'] != str(self.user.id):
            await self.send_json({
                'type': 'user.typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'channel_id': event['channel_id']
            })

    async def user_stopped_typing(self, event):
        """User stopped typing"""
        await self.send_json({
            'type': 'user.stopped_typing',
            'user_id': event['user_id'],
            'channel_id': event['channel_id']
        })

    async def user_online(self, event):
        """Send online status"""
        if event['user_id'] != str(self.user.id):
            await self.send_json({
                'type': 'user.online',
                'user_id': event['user_id'],
                'username': event['username']
            })

    async def user_offline(self, event):
        """Send offline status"""
        if event['user_id'] != str(self.user.id):
            await self.send_json({
                'type': 'user.offline',
                'user_id': event['user_id']
            })

    async def reaction_added(self, event):
        """Send reaction added"""
        await self.send_json({
            'type': 'reaction.added',
            'message_id': event['message_id'],
            'emoji': event['emoji'],
            'user_id': event['user_id']
        })
        
    async def reaction_removed(self, event):
        """Send reaction removed (Missing in original prompt)"""
        await self.send_json({
            'type': 'reaction.removed',
            'message_id': event['message_id'],
            'emoji': event['emoji'],
            'user_id': event['user_id']
        })

    # --- Database operations (wrapped with database_sync_to_async) ---

    @database_sync_to_async
    def is_workspace_member(self):
        from apps.workspaces.models import WorkspaceMember
        return WorkspaceMember.objects.filter(
            workspace_id=self.workspace_id,
            user=self.user
        ).exists()

    @database_sync_to_async
    def is_channel_member(self, channel_id):
        return ChannelMember.objects.filter(
            channel_id=channel_id,
            user=self.user
        ).exists()
        
    @database_sync_to_async
    def get_message(self, message_id):
        # Helper to get message object for channel_id
        return Message.objects.get(id=message_id)

    @database_sync_to_async
    def save_message(self, channel_id, content, parent_message_id=None, attachments=None):
        return Message.objects.create(
            channel_id=channel_id,
            sender=self.user,
            content=content,
            parent_message_id=parent_message_id,
            attachments=attachments or []
        )

    @database_sync_to_async
    def serialize_message(self, message):
        # Must import serializer within function to avoid circular import if needed
        from .serializers import MessageSerializer
        # Pass a dummy request for context
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = Request(factory.get('/'))
        return MessageSerializer(message, context={'request': request}).data

    @database_sync_to_async
    def extract_mentions(self, content):
        import re
        # Extract @username mentions
        mentions = re.findall(r'@(\w+)', content)
        user_ids = User.objects.filter(
            username__in=mentions
        ).values_list('id', flat=True)
        return list(user_ids)

    @database_sync_to_async
    def update_last_read(self, channel_id):
        ChannelMember.objects.filter(
            channel_id=channel_id,
            user=self.user
        ).update(last_read_at=timezone.now())

    @database_sync_to_async
    def edit_message(self, message_id, new_content):
        # Ensures only the sender can edit
        message = Message.objects.get(id=message_id, sender=self.user, is_deleted=False)
        message.content = new_content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        return message

    @database_sync_to_async
    def delete_message(self, message_id):
        # Soft delete. Also ensures only the sender can delete
        message = Message.objects.get(id=message_id, sender=self.user)
        channel_id = message.channel_id
        message.is_deleted = True
        message.save()
        return channel_id

    @database_sync_to_async
    def add_reaction(self, message_id, emoji):
        return MessageReaction.objects.get_or_create(
            message_id=message_id,
            user=self.user,
            emoji=emoji
        )
        
    @database_sync_to_async
    def remove_reaction(self, message_id, emoji):
        return MessageReaction.objects.filter(
            message_id=message_id,
            user=self.user,
            emoji=emoji
        ).delete()