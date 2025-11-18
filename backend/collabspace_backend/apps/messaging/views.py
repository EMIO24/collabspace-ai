from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Max, Count
from django.utils import timezone
from .models import Channel, Message, DirectMessage, ChannelMember, MessageReaction
from .serializers import *
from .permissions import IsChannelMember, CanManageChannel
from .pagination import MessageCursorPagination
from apps.authentication.models import User # Assuming User model location


class ChannelViewSet(viewsets.ModelViewSet):
    """Channel CRUD operations"""
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]
    
    # Use CanManageChannel for actions that require admin/creator rights
    # Use IsChannelMember for actions that require membership

    def get_queryset(self):
        workspace_id = self.request.query_params.get('workspace')
        
        # Only return channels the user is a member of, for the specified workspace
        return Channel.objects.filter(
            workspace_id=workspace_id,
            members=self.request.user
        ).select_related('created_by').prefetch_related('members').order_by('name')

    def get_permissions(self):
        # Apply CanManageChannel permission to specific actions
        if self.action in ['update', 'partial_update', 'destroy', 'add_member', 'remove_member', 'archive', 'unarchive']:
            self.permission_classes = [IsAuthenticated, CanManageChannel]
        elif self.action in ['retrieve']:
             self.permission_classes = [IsAuthenticated, IsChannelMember]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Create channel and automatically add the creator as a member/admin
        channel = serializer.save(created_by=self.request.user)
        channel.add_member(self.request.user, role='admin')

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List channel members"""
        channel = self.get_object()
        # Ensure only channel members can view the member list
        if not IsChannelMember().has_object_permission(request, self, channel):
            return Response({'detail': 'Not a member of this channel.'}, status=status.HTTP_403_FORBIDDEN)
            
        members = ChannelMember.objects.filter(channel=channel).select_related('user')
        serializer = ChannelMemberSerializer(members, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageChannel])
    def add_member(self, request, pk=None):
        channel = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')

        try:
            user_to_add = User.objects.get(id=user_id)
            if not user_to_add.workspacemember_set.filter(workspace=channel.workspace).exists():
                return Response({'detail': 'User is not a member of the workspace.'}, status=status.HTTP_400_BAD_REQUEST)
                
            member, created = channel.add_member(user_to_add, role)
            status_message = 'member added' if created else 'member already exists'
            return Response({'status': status_message, 'user_id': user_id})
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageChannel])
    def remove_member(self, request, pk=None):
        channel = self.get_object()
        user_id = request.data.get('user_id')

        try:
            user_to_remove = User.objects.get(id=user_id)
            if user_to_remove == channel.created_by:
                return Response({'detail': 'Cannot remove channel creator.'}, status=status.HTTP_403_FORBIDDEN)
                
            deleted_count, _ = channel.remove_member(user_to_remove)
            if deleted_count > 0:
                return Response({'status': 'member removed', 'user_id': user_id})
            return Response({'detail': 'User was not a member.'}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageChannel])
    def archive(self, request, pk=None):
        channel = self.get_object()
        if not channel.is_archived:
            channel.archive() # Uses model method
        return Response({'status': 'channel archived'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageChannel])
    def unarchive(self, request, pk=None):
        channel = self.get_object()
        if channel.is_archived:
            channel.is_archived = False
            channel.save(update_fields=['is_archived'])
        return Response({'status': 'channel unarchived'})


class MessageViewSet(viewsets.ModelViewSet):
    """Message operations"""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsChannelMember]
    pagination_class = MessageCursorPagination # Use cursor pagination for message history

    def get_queryset(self):
        channel_id = self.request.query_params.get('channel')
        
        # Check if channel_id is provided, otherwise return empty
        if not channel_id:
            return Message.objects.none()
            
        # Ensure user is a member of the channel
        if not ChannelMember.objects.filter(channel_id=channel_id, user=self.request.user).exists():
            return Message.objects.none()

        # Filter by channel, exclude soft-deleted, and optimize lookups
        return Message.objects.filter(
            channel_id=channel_id,
            is_deleted=False
        ).select_related('sender', 'parent_message__sender').prefetch_related('reactions', 'mentions', 'replies')
        
    def get_permissions(self):
        # Allow PUT/PATCH/DELETE only if the user is the sender
        if self.action in ['update', 'partial_update', 'destroy']:
            # The IsChannelMember is already applied via get_permissions
            self.permission_classes = [IsAuthenticated, IsChannelMember]
            # Further check in perform_update/destroy
        return super().get_permissions()

    def perform_create(self, serializer):
        # REST fallback for sending messages
        channel_id = self.request.data.get('channel')
        channel = Channel.objects.get(id=channel_id)

        # Check permission before saving
        if not IsChannelMember().has_object_permission(self.request, self, channel):
            raise PermissionDenied("Not a member of this channel.")

        message = serializer.save(sender=self.request.user, is_edited=False)
        # Note: Mentions and notifications would be handled by signals/async tasks

    def perform_update(self, serializer):
        # Only allow the sender to edit
        if serializer.instance.sender != self.request.user:
            raise PermissionDenied("You can only edit your own messages.")
            
        serializer.save(is_edited=True, edited_at=timezone.now())

    def perform_destroy(self, instance):
        # Only allow the sender to soft-delete
        if instance.sender != self.request.user:
            raise PermissionDenied("You can only delete your own messages.")
            
        instance.delete_soft() # Use soft delete method

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChannelMember])
    def add_reaction(self, request, pk=None):
        message = self.get_object()
        emoji = request.data.get('emoji')

        if not emoji:
             return Response({'detail': 'Emoji is required.'}, status=status.HTTP_400_BAD_REQUEST)

        MessageReaction.objects.get_or_create(
            message=message,
            user=request.user,
            emoji=emoji
        )
        # In a real app, this would also trigger a WebSocket broadcast
        return Response({'status': 'reaction added'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChannelMember])
    def remove_reaction(self, request, pk=None):
        message = self.get_object()
        emoji = request.data.get('emoji')

        if not emoji:
             return Response({'detail': 'Emoji is required.'}, status=status.HTTP_400_BAD_REQUEST)
             
        deleted_count, _ = MessageReaction.objects.filter(
            message=message,
            user=request.user,
            emoji=emoji
        ).delete()
        
        if deleted_count > 0:
            return Response({'status': 'reaction removed'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Reaction not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChannelMember, CanManageChannel])
    def pin(self, request, pk=None):
        message = self.get_object()
        message.is_pinned = True
        message.save(update_fields=['is_pinned'])
        return Response({'status': 'message pinned'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChannelMember, CanManageChannel])
    def unpin(self, request, pk=None):
        message = self.get_object()
        message.is_pinned = False
        message.save(update_fields=['is_pinned'])
        return Response({'status': 'message unpinned'})

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search messages within a specific channel (requires channel ID in query)"""
        query = request.query_params.get('q')
        channel_id = request.query_params.get('channel')
        
        if not query or not channel_id:
            return Response({'detail': 'Query and Channel ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure user is a member of the channel before searching
        if not ChannelMember.objects.filter(channel_id=channel_id, user=request.user).exists():
            return Response({'detail': 'Not a member of this channel.'}, status=status.HTTP_403_FORBIDDEN)

        messages = Message.objects.filter(
            channel_id=channel_id,
            content__icontains=query,
            is_deleted=False
        ).select_related('sender').prefetch_related('reactions', 'mentions')[:50] # Limit results
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class DirectMessageViewSet(viewsets.ModelViewSet):
    """Direct messages"""
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]
    
    # Optional: Use MessageCursorPagination if the list is likely to be long
    # pagination_class = MessageCursorPagination

    def get_queryset(self):
        # Get all DM conversations for current user (sender or recipient)
        return DirectMessage.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        ).select_related('sender', 'recipient').order_by('created_at')

    def perform_create(self, serializer):
        recipient_id = self.request.data.get('recipient')
        if not recipient_id:
            raise serializers.ValidationError({"recipient": "Recipient ID is required."})
            
        # Ensure recipient is a valid user and not the sender
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"recipient": "Recipient user not found."})
            
        if self.request.user == recipient:
            raise serializers.ValidationError({"recipient": "Cannot send DM to self."})
            
        serializer.save(sender=self.request.user, recipient=recipient)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        dm = self.get_object()
        # Only the recipient can mark a message as read
        if dm.recipient == request.user and not dm.is_read:
            dm.is_read = True
            dm.read_at = timezone.now()
            dm.save(update_fields=['is_read', 'read_at'])
            return Response({'status': 'marked as read'}, status=status.HTTP_200_OK)
            
        return Response({'status': 'no change or not authorized'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Get list of unique DM conversations (user-to-user) with last message timestamp"""
        # Finds unique pairs of (user1, user2) involved in DMs with request.user, regardless of sender/recipient role
        # This is a complex query to get unique conversations. A better approach for scalability might involve a 'Conversation' model.
        
        # Identify the 'other user' in each conversation
        conversations_raw = DirectMessage.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).annotate(
            other_user_id=Case(
                When(sender=request.user, then=F('recipient_id')),
                default=F('sender_id'),
                output_field=models.UUIDField()
            )
        ).values('other_user_id').annotate(
            last_message_at=Max('created_at')
        ).order_by('-last_message_at')
        
        # Get the actual last message for each conversation (this is the expensive part)
        # For simplicity and performance, we'll return the 'other_user_id' and the timestamp, 
        # and let the frontend fetch the last message/user details.

        conversation_list = []
        for conv in conversations_raw:
            other_user = User.objects.get(id=conv['other_user_id'])
            
            # Get the actual last message object
            last_message = DirectMessage.objects.filter(
                Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user)
            ).order_by('-created_at').first()
            
            last_message_data = DirectMessageSerializer(last_message).data if last_message else None
            
            conversation_list.append({
                'other_user': {
                    'id': str(other_user.id),
                    'username': other_user.username,
                    'full_name': other_user.get_full_name(),
                },
                'last_message_at': conv['last_message_at'],
                'last_message': last_message_data
            })

        return Response(conversation_list)


class MessageSearchView(APIView):
    """Search messages across channels in a workspace"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q')
        workspace_id = request.query_params.get('workspace')
        
        if not query or not workspace_id:
            return Response({'detail': 'Query and Workspace ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Search in channels user is a member of for the specified workspace
        messages = Message.objects.filter(
            channel__workspace_id=workspace_id,
            channel__members=request.user, # Only search in channels the user is a member of
            content__icontains=query,
            is_deleted=False
        ).select_related('channel', 'sender').order_by('-created_at')[:50] # Limit results

        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)