import json
import re
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from .models import Channel, ChannelMember, Message, Workspace

# User model reference from settings
User = settings.AUTH_USER_MODEL 


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Handles WebSocket connections for real-time messaging within a specific workspace.
    Manages presence, messages, typing indicators, and read receipts.
    """
    
    async def connect(self):
        """Handle WebSocket connection and authentication."""
        self.user = self.scope["user"]
        # The workspace_id is captured by the routing URL pattern
        self.workspace_id = self.scope['url_route']['kwargs']['workspace_id']
        self.workspace_group_name = f'workspace_{self.workspace_id}'

        if not self.user.is_authenticated:
            # The JWTAuthMiddleware should handle non-auth, but we ensure closure
            await self.close()
            return
        
        # 1. Accept connection
        await self.accept()

        # 2. Join the dedicated workspace group (for presence updates)
        await self.channel_layer.group_add(
            self.workspace_group_name,
            self.channel_name
        )
        
        # 3. Broadcast online status to the workspace room
        await self.channel_layer.group_send(
            self.workspace_group_name,
            {
                'type': 'user.online',
                'user_id': str(self.user.id),
                'username': self.user.username,
            }
        )
        
        # 4. Join all channel groups the user is a member of in this workspace
        user_channel_groups = await self.get_user_channel_groups(self.user, self.workspace_id)
        for group_name in user_channel_groups:
            await self.channel_layer.group_add(group_name, self.channel_name)

    async def disconnect(self, close_code):
        """Handle disconnection."""
        
        # 1. Send offline status
        await self.channel_layer.group_send(
            self.workspace_group_name,
            {
                'type': 'user.offline',
                'user_id': str(self.user.id),
                'username': self.user.username,
            }
        )
        
        # 2. Leave the workspace room
        await self.channel_layer.group_discard(
            self.workspace_group_name,
            self.channel_name
        )
        
        # 3. Leave all joined channel groups
        user_channel_groups = await self.get_user_channel_groups(self.user, self.workspace_id)
        for group_name in user_channel_groups:
            await self.channel_layer.group_discard(group_name, self.channel_name)


    # == WebSocket Receive Handler ==
    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get('type')
        
        if not message_type:
            await self.send_json({'error': 'Missing message type'})
            return

        # Replace dot notation with underscore for method lookup: 'message.send' -> 'handle_message_send'
        handler_method = getattr(self, f"handle_{message_type.replace('.', '_')}", None)
        
        if handler_method:
            await handler_method(content)
        else:
            await self.send_json({'error': f"Unknown message type: {message_type}"})

    # == Command Implementations (Handling client requests) ==

    async def handle_message_send(self, data):
        """Save message to DB and broadcast."""
        channel_id = data.get('channel_id')
        content = data.get('content')
        parent_message_id = data.get('parent_message_id')
        
        if not channel_id or not content:
            await self.send_json({'error': 'Missing channel_id or content.'})
            return

        # 1. Save and serialize message (including validation and mention extraction)
        result = await self.create_and_serialize_message(
            channel_id, 
            content, 
            self.user, 
            parent_message_id
        )
        
        if result['error']:
            await self.send_json({'error': result['error']})
            return
            
        message_data = result['message']
        
        # 2. Broadcast the message to the channel group
        channel_group_name = f'channel_{channel_id}'
        await self.channel_layer.group_send(
            channel_group_name,
            {
                'type': 'message.new', # Group handler method
                'message': message_data,
            }
        )
        
        # 3. Send direct notifications to mentioned users (optional)
        for user_id in result['mentioned_user_ids']:
            await self.channel_layer.group_send(
                f'user_{user_id}', # Group for a specific user's channels
                {
                    'type': 'notification.mention',
                    'message': message_data,
                }
            )


    async def handle_typing_start(self, data):
        """Broadcast typing indicator."""
        channel_id = data.get('channel_id')
        if not channel_id: return
        
        if not await self.is_user_channel_member(self.user.id, channel_id): return

        await self.channel_layer.group_send(
            f"channel_{channel_id}",
            {
                'type': 'user.typing',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'channel_id': str(channel_id),
                'is_typing': True,
            }
        )
        
    async def handle_typing_stop(self, data):
        """Stop typing indicator."""
        channel_id = data.get('channel_id')
        if not channel_id: return
        
        if not await self.is_user_channel_member(self.user.id, channel_id): return

        await self.channel_layer.group_send(
            f"channel_{channel_id}",
            {
                'type': 'user.typing',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'channel_id': str(channel_id),
                'is_typing': False,
            }
        )
        
    async def handle_message_read(self, data):
        """Update last_read_at for the channel member."""
        channel_id = data.get('channel_id')
        
        if not channel_id:
            await self.send_json({'error': 'Missing channel_id for read receipt.'})
            return

        # 1. Update last_read_at in the database
        member_data = await self.update_channel_last_read(self.user.id, channel_id)
        
        if not member_data:
            return
            
        # 2. Broadcast the read receipt event to the channel group
        await self.channel_layer.group_send(
            f"channel_{channel_id}",
            {
                'type': 'message.read',
                'user_id': str(self.user.id),
                'channel_id': str(channel_id),
                'last_read_at': member_data['last_read_at'],
            }
        )

    async def handle_presence_update(self, data):
        """Broadcast custom presence updates (e.g., set away status)."""
        status = data.get('status')
        if status in ['away', 'busy']:
             await self.channel_layer.group_send(
                self.workspace_group_name,
                {
                    'type': 'user.presence',
                    'user_id': str(self.user.id),
                    'status': status,
                }
            )

    # == Group Handler Methods (The 'type' methods - sent TO client) ==

    async def message_new(self, event):
        """Send new message to client."""
        await self.send_json({
            'type': 'message.new',
            'message': event['message'],
        })

    async def message_read(self, event):
        """Send read receipt update."""
        await self.send_json({
            'type': 'message.read',
            'user_id': event['user_id'],
            'channel_id': event['channel_id'],
            'last_read_at': event['last_read_at'],
        })

    async def user_typing(self, event):
        """Send typing indicator."""
        # Prevent echoing back to the sender
        if event.get('user_id') != str(self.user.id):
            await self.send_json({
                'type': 'user.typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'channel_id': event['channel_id'],
                'is_typing': event['is_typing'],
            })

    async def user_online(self, event):
        """Send online status."""
        if event.get('user_id') != str(self.user.id):
            await self.send_json({
                'type': 'presence.update',
                'status': 'online',
                'user_id': event['user_id'],
                'username': event['username'],
            })

    async def user_offline(self, event):
        """Send offline status."""
        if event.get('user_id') != str(self.user.id):
            await self.send_json({
                'type': 'presence.update',
                'status': 'offline',
                'user_id': event['user_id'],
                'username': event['username'],
            })

    async def user_presence(self, event):
        """Send custom presence status."""
        if event.get('user_id') != str(self.user.id):
            await self.send_json({
                'type': 'presence.update',
                'status': event['status'],
                'user_id': event['user_id'],
            })

    # Other message types (message.updated, message.deleted) would also be implemented here

    # == Database Synchronization Methods ==

    @sync_to_async
    def get_user_channel_groups(self, user, workspace_id):
        """Fetch group names for all channels the user is a member of in this workspace."""
        try:
            # Assuming a Workspace ID check is needed here
            if not Workspace.objects.filter(id=workspace_id).exists(): return []

            channels = Channel.objects.filter(
                workspace_id=workspace_id, 
                channelmember__user=user, 
                is_archived=False
            )
            # Group name format: 'channel_<UUID>'
            return [f"channel_{c.id}" for c in channels]
        except Exception as e:
            print(f"Error fetching channels for user: {e}")
            return []

    @sync_to_async
    def is_user_channel_member(self, user_id, channel_id):
        """Check if a user is an active member of a channel."""
        return ChannelMember.objects.filter(
            user_id=user_id, 
            channel_id=channel_id
        ).exists()

    @sync_to_async
    def create_and_serialize_message(self, channel_id, content, sender, parent_message_id=None):
        """Saves a message to the database, handles mentions, and serializes it."""
        
        result = {'message': None, 'error': None, 'mentioned_user_ids': []}
        
        try:
            # 1. Validation: Check if user is a member
            if not ChannelMember.objects.filter(user=sender, channel_id=channel_id).exists():
                result['error'] = 'User is not a member of this channel.'
                return result
                
            # 2. Find parent message (for threading)
            parent_message = None
            if parent_message_id:
                try:
                    parent_message = Message.objects.get(id=parent_message_id, channel_id=channel_id)
                except Message.DoesNotExist:
                    result['error'] = 'Parent message not found.'
                    return result
            
            # 3. Create the message
            message = Message.objects.create(
                channel_id=channel_id,
                sender=sender,
                content=content,
                parent_message=parent_message
            )
            
            # 4. Handle Mentions
            # Find usernames matching '@username' pattern
            mentioned_usernames = re.findall(r'@(\w+)', content)
            
            if mentioned_usernames:
                # Filter users down to only those who are members of the current channel
                mentioned_users = User.objects.filter(
                    username__in=mentioned_usernames, 
                    channelmember__channel_id=channel_id
                ).distinct()
                
                message.mentions.set(mentioned_users)
                result['mentioned_user_ids'] = list(mentioned_users.values_list('id', flat=True))
                
            # 5. Update ChannelMember last_read_at for the sender
            ChannelMember.objects.filter(user=sender, channel_id=channel_id).update(last_read_at=timezone.now())
            
            # 6. Simple Serialization for broadcast
            result['message'] = {
                'id': str(message.id),
                'channel_id': str(message.channel_id),
                'sender': {'id': str(sender.id), 'username': sender.username},
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'parent_message_id': str(message.parent_message_id) if message.parent_message_id else None,
                'mentions': list(message.mentions.values('id', 'username')),
                'reactions': [], 
            }
            return result
            
        except Exception as e:
            result['error'] = f"Database error on message creation: {e}"
            return result

    @sync_to_async
    def update_channel_last_read(self, user_id, channel_id):
        """Updates the ChannelMember's last_read_at timestamp."""
        try:
            member = ChannelMember.objects.get(user_id=user_id, channel_id=channel_id)
            member.last_read_at = timezone.now()
            member.save(update_fields=['last_read_at', 'updated_at'])
            return {'last_read_at': member.last_read_at.isoformat()}
        except ChannelMember.DoesNotExist:
            # User is not a member, no update possible
            return None