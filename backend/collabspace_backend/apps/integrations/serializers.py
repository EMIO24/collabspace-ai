from rest_framework import serializers
from .models import Integration, Webhook


class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for Webhook model"""
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    service_type = serializers.CharField(source='integration.service_type', read_only=True)
    
    class Meta:
        model = Webhook
        fields = [
            'id',
            'integration',
            'integration_name',
            'service_type',
            'service_event',
            'external_id',
            'target_url',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret': {'write_only': True},  # Never expose webhook secret
        }


class IntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Integration model"""
    webhooks = WebhookSerializer(many=True, read_only=True)
    webhook_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Integration
        fields = [
            'id',
            'service_type',
            'name',
            'client_id',
            'access_token',
            'refresh_token',
            'token_expiry',
            'settings',
            'is_active',
            'created_at',
            'updated_at',
            'webhooks',
            'webhook_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'access_token': {'write_only': True},  # Never expose in responses
            'refresh_token': {'write_only': True},  # Never expose in responses
            'client_id': {'write_only': True},  # Only accept in requests
        }
    
    def get_webhook_count(self, obj):
        """Return count of webhooks for this integration"""
        return obj.webhooks.count()
    
    def validate_service_type(self, value):
        """Validate service type"""
        valid_types = ['github', 'slack', 'jira']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid service type. Must be one of: {', '.join(valid_types)}"
            )
        return value
    
    def validate_settings(self, value):
        """Validate settings JSON field"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Settings must be a dictionary")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        service_type = data.get('service_type')
        settings = data.get('settings', {})
        
        # Validate required settings per service type
        if service_type == 'github':
            required_fields = ['repo_owner', 'repo_name']
            missing = [f for f in required_fields if f not in settings]
            if missing:
                raise serializers.ValidationError({
                    'settings': f"Missing required fields for GitHub: {', '.join(missing)}"
                })
        
        elif service_type == 'slack':
            required_fields = ['team_id', 'workspace_name']
            missing = [f for f in required_fields if f not in settings]
            if missing:
                raise serializers.ValidationError({
                    'settings': f"Missing required fields for Slack: {', '.join(missing)}"
                })
        
        elif service_type == 'jira':
            required_fields = ['jira_url', 'project_key']
            missing = [f for f in required_fields if f not in settings]
            if missing:
                raise serializers.ValidationError({
                    'settings': f"Missing required fields for Jira: {', '.join(missing)}"
                })
        
        return data


class IntegrationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing integrations"""
    webhook_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Integration
        fields = [
            'id',
            'service_type',
            'name',
            'is_active',
            'created_at',
            'webhook_count'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_webhook_count(self, obj):
        return obj.webhooks.count()