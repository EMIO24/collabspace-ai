from rest_framework import serializers
from .models import Channel, Message, DirectMessage, ChannelMember, MessageReaction
from django.db.models import Count, Max, Q
from django.utils import timezone
# Assuming profile/user structure for get_user methods:


class ChannelMemberSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChannelMember
        fields = ['user', 'role', 'created_at', 'last_read_at', 'unread_count', 'notifications_enabled'] # changed joined_at to created_at

    def get_user(self, obj):
        # Use obj.user to access the related User object
        user = obj.user
        return {
            'id': str(user.id),
            'username': user.username,
            'full_name': user.get_full_name(),
            'avatar': getattr(user, 'profile', None).avatar_url if hasattr(user, 'profile') else None
        }

    def get_unread_count(self, obj):
        # Calls the method defined on the ChannelMember model
        return obj.get_unread_count()


class MessageReactionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = MessageReaction
        fields = ['emoji', 'user', 'created_at']

    def get_user(self, obj):
        # Use obj.user to access the related User object
        user = obj.user
        return {
            'id': str(user.id),
            'username': user.username
        }


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reactions_summary = serializers.SerializerMethodField()
    reply_count = serializers.IntegerField(source='replies.count', read_only=True)
    
    # Nested field for parent message preview (optional, adjust if too deep)
    parent_message_preview = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['sender', 'is_edited', 'edited_at']

    def get_sender(self, obj):
        user = obj.sender
        if not user:
             return {'id': None, 'username': 'deleted_user', 'full_name': 'Deleted User', 'avatar': None}
             
        return {
            'id': str(user.id),
            'username': user.username,
            'full_name': user.get_full_name(),
            'avatar': getattr(user, 'profile', None).avatar_url if hasattr(user, 'profile') else None
        }

    def get_reactions_summary(self, obj):
        # Group reactions by emoji with count
        reactions = obj.reactions.values('emoji').annotate(count=Count('id'))
        return {r['emoji']: r['count'] for r in reactions}

    def get_parent_message_preview(self, obj):
        if obj.parent_message:
            # Only serialize a minimal version to avoid recursion
            return {
                'id': str(obj.parent_message.id),
                'content': obj.parent_message.content[:100] + '...' if len(obj.parent_message.content) > 100 else obj.parent_message.content,
                'sender_username': obj.parent_message.sender.username if obj.parent_message.sender else 'deleted_user',
                'created_at': obj.parent_message.created_at
            }
        return None


class ChannelSerializer(serializers.ModelSerializer):
    members_count = serializers.IntegerField(source='members.count', read_only=True)
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    # Add created_by details
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Channel
        fields = '__all__'
        read_only_fields = ['created_by']

    def get_created_by(self, obj):
        user = obj.created_by
        if not user:
            return None
        return {
            'id': str(user.id),
            'username': user.username,
        }

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                # Use obj.channelmember_set for reverse lookup if related_name isn't used on ChannelMember model
                # Assuming ChannelMember.objects.get works based on model definition
                member = ChannelMember.objects.get(channel=obj, user=request.user)
                # Calls the get_unread_count method on the member instance
                return member.get_unread_count()
            except ChannelMember.DoesNotExist:
                return 0
        return 0

    def get_last_message(self, obj):
        # Efficiently fetch the last message without loading the entire queryset
        last_msg = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_msg:
            # Use a minimal serializer to avoid recursion and excessive data
            return {
                'id': str(last_msg.id),
                'content': last_msg.content[:50] + '...',
                'sender_username': last_msg.sender.username if last_msg.sender else 'deleted_user',
                'created_at': last_msg.created_at
            }
        return None


class DirectMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()

    class Meta:
        model = DirectMessage
        fields = '__all__'
        read_only_fields = ['sender', 'is_read', 'read_at']

    def get_sender(self, obj):
        user = obj.sender
        return {
            'id': str(user.id),
            'username': user.username,
            'full_name': user.get_full_name()
        }

    def get_recipient(self, obj):
        user = obj.recipient
        return {
            'id': str(user.id),
            'username': user.username,
            'full_name': user.get_full_name()
        }