from rest_framework import viewsets, mixins, filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404

from .models import Channel, Message, DirectMessage, ChannelMember, MessageReaction
from .serializers import (
    ChannelSerializer, ChannelDetailSerializer, MessageSerializer, 
    MessageCreateSerializer, DirectMessageSerializer, SimpleUserSerializer,
    MessageReactionSerializer
)
from .pagination import MessageCursorPagination

# Get the channel layer instance for real-time fallback
channel_layer = get_channel_layer()

class StandardPagination(PageNumberPagination):
    """Standard pagination for non-message lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ChannelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows channels to be viewed, created, or edited.
    Users can only see channels they are a member of, or public channels.
    """
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Use a detailed serializer for retrieve and update actions
        if self.action in ('retrieve', 'update', 'partial_update'):
            return ChannelDetailSerializer
        return ChannelSerializer

    def get_queryset(self):
        # Only show channels where the user is a member OR the channel is public
        user = self.request.user
        return Channel.objects.filter(
            Q(members=user) | Q(channel_type='public')
        ).distinct().prefetch_related('members')
    
    def perform_create(self, serializer):
        # When a channel is created, the creator is set as the creator and added as a member (admin role)
        channel = serializer.save(created_by=self.request.user)
        ChannelMember.objects.create(channel=channel, user=self.request.user, role='admin')

    def destroy(self, request, *args, **kwargs):
        """Standard destroy is disabled. Use /archive/ action."""
        return Response({"detail": "Use the /archive/ action to close a channel."}, 
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)
                        
    # --- Custom Actions ---

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """Adds a user to a channel. Requires channel admin privileges."""
        channel = self.get_object()
        user_id = request.data.get('user_id')

        # Simple check: Only admins/creator of the channel can add members
        if request.user != channel.created_by and not channel.channelmember_set.filter(user=request.user, role='admin').exists():
            return Response({"detail": "Only channel administrators can add members."}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            new_member = self.get_queryset().model.members.model.objects.get(id=user_id)
        except self.get_queryset().model.members.model.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if channel.members.filter(id=user_id).exists():
            return Response({"detail": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST)

        ChannelMember.objects.create(channel=channel, user=new_member, role='member')
        return Response(SimpleUserSerializer(new_member).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        """Removes a user from a channel. Requires channel admin privileges."""
        channel = self.get_object()
        user_id = request.data.get('user_id')

        # Simple check: Only admins/creator of the channel can remove members
        if request.user != channel.created_by and not channel.channelmember_set.filter(user=request.user, role='admin').exists():
            return Response({"detail": "Only channel administrators can remove members."}, status=status.HTTP_403_FORBIDDEN)

        try:
            member_to_remove = ChannelMember.objects.get(channel=channel, user__id=user_id)
            member_to_remove.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ChannelMember.DoesNotExist:
            return Response({"detail": "User is not a member of this channel."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archives a channel."""
        channel = self.get_object()
        # Permission check: Only creator or admin can archive
        if request.user != channel.created_by and not channel.channelmember_set.filter(user=request.user, role='admin').exists():
             return Response({"detail": "Only channel administrators can archive."}, status=status.HTTP_403_FORBIDDEN)
             
        channel.is_archived = True
        channel.save(update_fields=['is_archived'])
        return Response({'is_archived': True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchives a channel."""
        channel = self.get_object()
        # Permission check: Only creator or admin can unarchive
        if request.user != channel.created_by and not channel.channelmember_set.filter(user=request.user, role='admin').exists():
             return Response({"detail": "Only channel administrators can unarchive."}, status=status.HTTP_403_FORBIDDEN)

        channel.is_archived = False
        channel.save(update_fields=['is_archived'])
        return Response({'is_archived': False}, status=status.HTTP_200_OK)


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing, listing, creating, and editing messages in a specific channel.
    Uses cursor-based pagination for listing.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MessageCursorPagination # Use cursor pagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        channel_id = self.kwargs.get('channel_pk')
        if not channel_id:
            return Message.objects.none()

        # Check if user is a member of the channel
        if not Channel.objects.filter(id=channel_id, members=self.request.user).exists():
            return Message.objects.none()
            
        # Order by created_at descending, which is the required ordering for CursorPagination
        return Message.objects.filter(channel_id=channel_id).order_by('-created_at').prefetch_related('sender', 'mentions', 'reactions__user')

    def perform_create(self, serializer):
        channel_id = self.kwargs.get('channel_pk')
        channel = get_object_or_404(Channel, id=channel_id)
        sender = self.request.user
        
        # Security check: Ensure sender is a member of the channel
        if not ChannelMember.objects.filter(channel=channel, user=sender).exists():
            raise serializers.ValidationError({"detail": "User is not a member of this channel."})
            
        # 1. Save the message
        message = serializer.save(sender=sender, channel=channel)
        
        # 2. Extract mentions and save them (simplified extraction, a cleaner version is in consumer)
        mentioned_usernames = re.findall(r'@(\w+)', message.content)
        if mentioned_usernames:
            mentioned_users = channel.members.filter(username__in=mentioned_usernames).distinct()
            message.mentions.set(mentioned_users)
            
        # 3. Use Channels layer as a REST fallback broadcast
        if channel_layer:
            # Use the MessageSerializer to generate the data for the frontend
            data = MessageSerializer(message).data 
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel_id}',
                {
                    'type': 'message.new',
                    'message': data,
                }
            )

    def perform_update(self, serializer):
        # Update logic: Only sender can edit, and set is_edited flag
        message = self.get_object()
        if message.sender != self.request.user:
            return Response({"detail": "You do not have permission to edit this message."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer.save(is_edited=True, edited_at=timezone.now())

    def perform_destroy(self, instance):
        # Delete logic: Only sender can delete, or a channel admin
        channel = instance.channel
        is_admin = channel.channelmember_set.filter(user=self.request.user, role='admin').exists()
        
        if instance.sender != self.request.user and not is_admin:
            return Response({"detail": "You do not have permission to delete this message."}, status=status.HTTP_403_FORBIDDEN)
            
        instance.delete()
        # Optional: Broadcast deletion event via channel layer
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'message.deleted',
                    'message_id': str(instance.id),
                    'channel_id': str(channel.id),
                }
            )

    # --- Custom Actions ---

    @action(detail=True, methods=['post'], url_path='add-reaction')
    def add_reaction(self, request, pk=None, channel_pk=None):
        """Adds a reaction to a message."""
        message = self.get_object()
        serializer = MessageReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add the message and user to the validated data
        serializer.validated_data['message'] = message
        serializer.validated_data['user'] = request.user
        
        reaction = serializer.save()
        
        # Optional: Broadcast reaction event via channel layer
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel_pk}',
                {
                    'type': 'message.reaction.added',
                    'message_id': str(message.id),
                    'reaction': MessageReactionSerializer(reaction).data,
                }
            )
        return Response(MessageReactionSerializer(reaction).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='remove-reaction')
    def remove_reaction(self, request, pk=None, channel_pk=None):
        """Removes a reaction from a message."""
        message = self.get_object()
        emoji = request.data.get('emoji')

        if not emoji:
            return Response({"detail": "Emoji is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # User can only remove their own reaction
        reaction = get_object_or_404(MessageReaction, message=message, user=request.user, emoji=emoji)
        reaction_id = reaction.id
        reaction.delete()
        
        # Optional: Broadcast reaction removal event via channel layer
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel_pk}',
                {
                    'type': 'message.reaction.removed',
                    'message_id': str(message.id),
                    'reaction_id': str(reaction_id),
                    'user_id': str(request.user.id),
                }
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None, channel_pk=None):
        """Pins a message in the channel. Requires channel admin/moderator role."""
        message = self.get_object()
        channel = message.channel
        
        # Permission check: Only admins/creator can pin
        if not channel.channelmember_set.filter(user=request.user, role__in=['admin', 'moderator']).exists():
            return Response({"detail": "Only channel administrators can pin messages."}, status=status.HTTP_403_FORBIDDEN)
            
        message.is_pinned = True
        message.save(update_fields=['is_pinned'])
        
        # Optional: Broadcast pin event
        return Response({'is_pinned': True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None, channel_pk=None):
        """Unpins a message."""
        message = self.get_object()
        channel = message.channel
        
        # Permission check: Only admins/creator can unpin
        if not channel.channelmember_set.filter(user=request.user, role__in=['admin', 'moderator']).exists():
            return Response({"detail": "Only channel administrators can unpin messages."}, status=status.HTTP_403_FORBIDDEN)
            
        message.is_pinned = False
        message.save(update_fields=['is_pinned'])

        # Optional: Broadcast unpin event
        return Response({'is_pinned': False}, status=status.HTTP_200_OK)


class DirectMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing, listing, and creating direct messages.
    """
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        # Optimization: Group DMs by the other user involved in the conversation
        # This queryset focuses on individual messages, as requested
        return DirectMessage.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).order_by('created_at')

    def perform_create(self, serializer):
        # Set the sender to the current authenticated user before saving
        dm = serializer.save(sender=self.request.user)
        
        # Use Channels layer as a REST fallback broadcast to the recipient
        if channel_layer:
            data = DirectMessageSerializer(dm).data 
            async_to_sync(channel_layer.group_send)(
                f'user_{dm.recipient_id}', # The recipient's dedicated user group
                {
                    'type': 'notification.dm_received_rest', # Different type to avoid conflict with signal
                    'dm': data,
                }
            )

    @action(detail=False, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request):
        """Marks all DMs sent by a specific user as read."""
        other_user_id = request.data.get('user_id')
        
        if not other_user_id:
            return Response({"detail": "Missing user_id parameter."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark DMs received from the 'other_user_id' to the current user as read
        DirectMessage.objects.filter(
            sender__id=other_user_id, 
            recipient=request.user, 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({"status": f"All DMs from {other_user_id} marked as read."}, status=status.HTTP_200_OK)


class MessageSearchView(generics.ListAPIView):
    """
    API endpoint to search across channel messages accessible by the user.
    Allows optional filtering by channel_id.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    # Search fields include content and usernames of sender/mentions
    search_fields = ['content', 'sender__username', 'mentions__username']
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        channel_id = self.request.query_params.get('channel_id')

        # 1. Determine accessible channels
        accessible_channels = Channel.objects.filter(
            Q(members=user) | Q(channel_type='public')
        ).distinct()
        
        # 2. Scope search to a specific channel if provided
        if channel_id:
            if not accessible_channels.filter(id=channel_id).exists():
                 # User provided a channel_id but cannot access it
                 return Message.objects.none() 
            accessible_channels = accessible_channels.filter(id=channel_id)

        # 3. Filter messages within the accessible scope
        queryset = Message.objects.filter(
            channel__in=accessible_channels
        ).order_by('-created_at').prefetch_related('sender', 'mentions')

        return queryset