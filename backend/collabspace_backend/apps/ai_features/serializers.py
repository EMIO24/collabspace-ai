import uuid
from rest_framework import serializers
from .models import AIUsage, AIPromptTemplate, AIRateLimit
from .utils import estimate_tokens # Use local utility


# --- Model Serializers ---

class AIUsageSerializer(serializers.ModelSerializer):
    """Serializer for the AIUsage model."""
    estimated_cost = serializers.SerializerMethodField()

    class Meta:
        model = AIUsage
        fields = '__all__'

    def get_estimated_cost(self, obj):
        return obj.estimate_cost()

class AIPromptTemplateSerializer(serializers.ModelSerializer):
    """Serializer for the AIPromptTemplate model."""
    class Meta:
        model = AIPromptTemplate
        fields = '__all__'
        read_only_fields = ['created_by']

class AIRateLimitSerializer(serializers.ModelSerializer):
    """Serializer for the AIRateLimit model, showing quota status."""
    can_make_request = serializers.SerializerMethodField()
    requests_remaining_today = serializers.SerializerMethodField()
    requests_remaining_minute = serializers.SerializerMethodField()

    class Meta:
        model = AIRateLimit
        fields = ('user', 'plan_type', 'daily_limit', 'requests_today', 'tokens_today', 
                  'minute_limit', 'requests_this_minute', 'can_make_request', 
                  'requests_remaining_today', 'requests_remaining_minute')

    def get_can_make_request(self, obj):
        return obj.can_make_request()

    def get_requests_remaining_today(self, obj):
        # We must call reset_if_needed implicitly to ensure accurate counts
        obj.reset_if_needed()
        return max(0, obj.daily_limit - obj.requests_today)

    def get_requests_remaining_minute(self, obj):
        obj.reset_if_needed()
        return max(0, obj.minute_limit - obj.requests_this_minute)


# --- Input Serializers (API Validation) ---

class TaskAISummarizeSerializer(serializers.Serializer):
    task_description = serializers.CharField(max_length=5000)

class TaskAICreateSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=10000)
    workspace_id = serializers.UUIDField()
    project_id = serializers.UUIDField(required=False)

class TaskAIBreakdownSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(required=False)
    task_description = serializers.CharField(max_length=5000, required=False)
    num_subtasks = serializers.IntegerField(default=5, min_value=2, max_value=10)
    auto_create = serializers.BooleanField(default=False)

class TaskAIEstimateSerializer(serializers.Serializer):
    task_description = serializers.CharField(max_length=5000)
    project_context = serializers.CharField(max_length=5000, required=False)

class TaskAIPrioritySerializer(serializers.Serializer):
    task_description = serializers.CharField(max_length=5000)
    due_date = serializers.CharField(max_length=255, required=False)

class TaskAIAssigneeSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(required=False)
    task_description = serializers.CharField(max_length=5000, required=False)
    team_members = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )

class MeetingTranscribeSerializer(serializers.Serializer):
    transcript = serializers.CharField(max_length=50000)
    auto_create_tasks = serializers.BooleanField(default=False)
    project_id = serializers.UUIDField(required=False)
    
class AnalyticsForecastSerializer(serializers.Serializer):
    project_id = serializers.UUIDField()
    confidence_level = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        default='medium'
    )
    
class AssistantChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    context = serializers.JSONField(required=False)
    conversation_history = serializers.ListField(
        child=serializers.JSONField(),
        required=False
    )
    # This is validated by permissions.CanUseAdvancedAI in the view
    use_pro_model = serializers.BooleanField(default=False)