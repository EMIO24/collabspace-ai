from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notification operations (Read/List/Mark as Read/Clear)"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Fetching notifications for the authenticated user only
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark single notification as read"""
        try:
            notification = self.get_object()
            notification.mark_as_read()
            return Response({'status': 'marked as read'})
        except Notification.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all UNREAD notifications for the user as read"""
        from django.utils import timezone
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({'status': f'{updated_count} notifications marked as read'})

    @action(detail=False, methods=['delete'])
    def clear_all_read(self, request):
        """Delete all READ notifications for the user"""
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()
        
        return Response({'status': f'{deleted_count} read notifications cleared'})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get only unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        # Optional: Add pagination here if needed
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)


class NotificationPreferenceView(APIView):
    """Manage user notification preferences (GET and UPDATE)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve user preferences"""
        # get_or_create ensures preferences exist for a new user
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)

    def put(self, request):
        """Update user preferences (using partial for flexibility)"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        # Using partial=True allows sending only the fields to be updated
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Alias for put (partial update)"""
        return self.put(request)


class UnreadCountView(APIView):
    """Get unread notification count"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})