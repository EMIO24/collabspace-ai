from rest_framework import serializers
from django.utils.timesince import timesince
from .models import Notification, NotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for the in-app Notification model"""
    # Custom field to show how long ago the notification was created
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = '__all__'
        # These fields are set by the system, not the user via API
        read_only_fields = ['user', 'is_read', 'read_at', 'created_at', 'updated_at']

    def get_time_ago(self, obj):
        """Returns a string like '2 hours ago'"""
        return f"{timesince(obj.created_at)} ago"

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for the NotificationPreference model"""
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ['user']