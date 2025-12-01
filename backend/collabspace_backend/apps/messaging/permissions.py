from rest_framework import permissions
from .models import ChannelMember
import logging

logger = logging.getLogger(__name__)

class IsChannelMember(permissions.BasePermission):
    """Check if user is member of the channel"""

    def has_permission(self, request, view):
        # For POST requests to MessageViewSet, verify channel membership upfront
        if view.basename == 'message' and request.method == 'POST':
            channel_id = request.data.get('channel')
            
            logger.info(f"POST check - User: {request.user}, Channel ID: {channel_id}")
            
            if not channel_id:
                logger.warning("No channel_id provided in POST request")
                return False
            
            # 1. Check if user is explicitly a member
            is_member = ChannelMember.objects.filter(
                channel_id=channel_id,
                user=request.user
            ).exists()

            # 2. FIX: Check if user is the CREATOR (Owner) of the channel
            # This allows owners to post even if the membership record is missing
            if not is_member:
                # We need to fetch the channel to check ownership
                from .models import Channel
                try:
                    channel = Channel.objects.get(id=channel_id)
                    if channel.created_by == request.user:
                        is_member = True
                        logger.info("User is channel creator (implicit member)")
                except Channel.DoesNotExist:
                    pass # Will return False below
            
            logger.info(f"Is member: {is_member}")
            return is_member
        
        # For other requests, defer to has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        """Check for object-level permission (GET/PUT/DELETE on a specific object)"""
        # Get the channel from the object
        if hasattr(obj, 'channel'):
            channel = obj.channel
        else:  # Likely a Channel object itself
            channel = obj

        logger.info(f"Object permission check - User: {request.user}, Channel: {channel.id}, Method: {request.method}")
        
        # 1. Allow if user is the creator
        if channel.created_by == request.user:
            return True

        # 2. Ensure user is a member of the channel
        is_member = ChannelMember.objects.filter(
            channel=channel,
            user=request.user
        ).exists()
        
        logger.info(f"Is member: {is_member}")
        return is_member


class CanManageChannel(permissions.BasePermission):
    """Check if user can manage channel (admin/creator)"""

    def has_object_permission(self, request, view, obj):
        # Always allow the creator/owner
        if obj.created_by == request.user:
            return True

        # Check if user has permission to manage the channel via membership role
        try:
            member = ChannelMember.objects.get(channel=obj, user=request.user)
            return member.role == 'admin'
        except ChannelMember.DoesNotExist:
            return False