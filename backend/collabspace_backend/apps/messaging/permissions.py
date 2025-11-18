from rest_framework import permissions
from .models import ChannelMember

class IsChannelMember(permissions.BasePermission):
    """Check if user is member of the channel"""

    def has_permission(self, request, view):
        # Allow POST request to MessageViewSet if channel_id is provided and user is a member
        if view.basename == 'message' and request.method == 'POST':
            channel_id = request.data.get('channel')
            if not channel_id:
                return False
            return ChannelMember.objects.filter(
                channel_id=channel_id,
                user=request.user
            ).exists()
        return True # Handled in has_object_permission for list/detail views

    def has_object_permission(self, request, view, obj):
        """Check for object-level permission (GET/PUT/DELETE on a specific object)"""
        if hasattr(obj, 'channel'):
            channel = obj.channel
        else: # Likely a Channel object itself
            channel = obj

        # Ensure user is a member of the channel/message's channel
        return ChannelMember.objects.filter(
            channel=channel,
            user=request.user
        ).exists()

class CanManageChannel(permissions.BasePermission):
    """Check if user can manage channel (admin/creator)"""

    def has_object_permission(self, request, view, obj):
        # Check if user has permission to manage the channel (e.g., add/remove member, archive)
        try:
            member = ChannelMember.objects.get(channel=obj, user=request.user)
            # Must be an admin or the channel creator
            return member.role == 'admin' or obj.created_by == request.user
        except ChannelMember.DoesNotExist:
            return False