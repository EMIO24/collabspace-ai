from rest_framework import serializers
from django.db.models import Count, Q
from django.utils import timezone
from .models import Channel, Message, MessageReaction, DirectMessage, ChannelMember
from django.conf import settings

User = settings.AUTH_USER_MODEL

# Placeholder for a simplified User Serializer
class SimpleUserSerializer(serializers.ModelSerializer):
    """Minimal user details for references (sender, member, mention)."""
    class Meta:
        model = User
        fields = ('id', 'username')

class MessageReactionSerializer(serializers.ModelSerializer):
    """Serializer for message reactions, including custom creation/deletion fields."""
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = MessageReaction
        fields = ('id', 'user', 'emoji', 'created_at', 'message')
        read_only_fields = ('user', 'created_at', 'id')
        extra_kwargs = {'message': {'write_only': True, 'required': False}}
    
    def create(self, validated_data):
        # Enforce unique constraint by attempting to update if exists
        reaction, created = MessageReaction.objects.update_or_create(
            message=validated_data.get('message'),
            user=validated_data.get('user'),
            emoji=validated_data.get('emoji'),
            defaults={'created_at': timezone.now()}
        )
        return reaction


# --- Channel Serializers ---

class ChannelSerializer(serializers.ModelSerializer):
    """Serializer for listing channels (includes unread count)."""
    # Requires 'user' in context (context={'request': request})
    unread_count = serializers.SerializerMethodField() 

    class Meta:
        model = Channel
        fields = ('id', 'name', 'description', 'channel_type', 'is_archived', 'created_at', 'unread_count')
        read_only_fields = ('created_at', 'is_archived', 'unread_count')
        
    def get_unread_count(self, obj):
        """Calculates the number of unread messages for the requesting user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        try:
            member = ChannelMember.objects.get(channel=obj, user=request.user)
            last_read_at = member.last_read_at
            
            # Count messages created after the user's last read time
            if last_read_at:
                return obj.messages.filter(created_at__gt=last_read_at).count()
            
            # If never read, count all messages
            return obj.messages.count()
            
        except ChannelMember.DoesNotExist:
            return 0

class ChannelDetailSerializer(ChannelSerializer):
    """Serializer for detailed channel view (includes members)."""
    members = SimpleUserSerializer(many=True, read_only=True)
    
    class Meta(ChannelSerializer.Meta):
        fields = ChannelSerializer.Meta.fields + ('members', 'created_by')
        read_only_fields = ChannelSerializer.Meta.read_only_fields + ('created_by',)


# --- Message Serializers ---

class MessageSerializer(serializers.ModelSerializer):
    """Full message serializer for listing and retrieval."""
    sender = SimpleUserSerializer(read_only=True)
    mentions = SimpleUserSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = (
            'id', 'channel', 'sender', 'content', 'message_type', 'parent_message', 
            'mentions', 'attachments', 'reactions', 'is_edited', 'is_pinned', 
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'channel', 'sender', 'message_type', 'attachments', 'is_edited', 
            'is_pinned', 'created_at', 'updated_at', 'reactions'
        )

class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages (input only)."""
    # Note: sender and channel are set in the view
    class Meta:
        model = Message
        fields = ('content', 'parent_message', 'message_type', 'attachments')
        extra_kwargs = {
            'content': {'required': True},
            'message_type': {'required': False, 'default': 'text'},
            'attachments': {'required': False, 'default': []},
            'parent_message': {'required': False},
        }

# --- Direct Message Serializers ---

class DirectMessageSerializer(serializers.ModelSerializer):
    """Direct message serializer for listing, retrieval, and creation."""
    sender = SimpleUserSerializer(read_only=True)
    recipient = SimpleUserSerializer(read_only=True)
    
    # Recipient ID is write-only for creation
    recipient_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = DirectMessage
        fields = ('id', 'sender', 'recipient', 'recipient_id', 'content', 'is_read', 'read_at', 'created_at')
        read_only_fields = ('sender', 'recipient', 'is_read', 'read_at', 'created_at')
        
    def create(self, validated_data):
        # We need the recipient_id from validated_data to look up the recipient User object
        recipient_id = validated_data.pop('recipient_id', None)
        sender = validated_data.get('sender') # Sender is set by the view (request.user)
        
        if not recipient_id:
            raise serializers.ValidationError({"recipient_id": "Recipient ID must be provided."})
            
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"recipient_id": "Recipient user not found."})
            
        if sender == recipient:
             raise serializers.ValidationError({"recipient_id": "Cannot send a DM to yourself."})

        validated_data['recipient'] = recipient
        return super().create(validated_data)