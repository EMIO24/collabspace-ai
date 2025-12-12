import uuid
from rest_framework import serializers
from .models import AIUsage, AIPromptTemplate, AIRateLimit
from .utils import estimate_tokens


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
        try:
            return obj.can_make_request(feature_type='general', cost=1)
        except TypeError as e:
            print(f"Serializer: can_make_request error: {e}")
            obj.reset_if_needed()
            return obj.requests_today < obj.daily_limit

    def get_requests_remaining_today(self, obj):
        obj.reset_if_needed()
        return max(0, obj.daily_limit - obj.requests_today)

    def get_requests_remaining_minute(self, obj):
        obj.reset_if_needed()
        return max(0, obj.minute_limit - obj.requests_this_minute)


# --- Task AI Serializers ---

class TaskAISummarizeSerializer(serializers.Serializer):
    """Serializer for task summarization."""
    task_description = serializers.CharField(max_length=5000)


class TaskAICreateSerializer(serializers.Serializer):
    """Serializer for creating tasks from text."""
    text = serializers.CharField(max_length=10000)
    workspace_id = serializers.UUIDField()
    project_id = serializers.UUIDField(required=False)


class TaskAIBreakdownSerializer(serializers.Serializer):
    """Serializer for breaking down tasks into subtasks."""
    task_id = serializers.UUIDField(required=False, allow_null=True)
    task_description = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    num_subtasks = serializers.IntegerField(default=5, min_value=2, max_value=10)
    auto_create = serializers.BooleanField(default=False)
    
    def validate(self, data):
        """Ensure at least one of task_id or task_description is provided."""
        task_id = data.get('task_id')
        task_description = data.get('task_description')
        
        if not task_id and not task_description:
            raise serializers.ValidationError({
                'task_description': 'Either task_id or task_description must be provided.'
            })
        
        return data


class TaskAIEstimateSerializer(serializers.Serializer):
    """Serializer for task effort estimation."""
    task_description = serializers.CharField(max_length=5000)
    project_context = serializers.CharField(max_length=5000, required=False, allow_blank=True)


class TaskAIPrioritySerializer(serializers.Serializer):
    """Serializer for task priority suggestion."""
    task_description = serializers.CharField(max_length=5000)
    due_date = serializers.CharField(max_length=255, required=False, allow_blank=True)


class TaskAIAssigneeSerializer(serializers.Serializer):
    """Serializer for suggesting task assignee."""
    task_id = serializers.UUIDField(required=False, allow_null=True)
    task_description = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    team_members = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate(self, data):
        """Ensure at least one of task_id or task_description is provided."""
        task_id = data.get('task_id')
        task_description = data.get('task_description')
        
        if not task_id and not task_description:
            raise serializers.ValidationError({
                'task_description': 'Either task_id or task_description must be provided.'
            })
        
        return data


class TaskAIDependencySerializer(serializers.Serializer):
    """Serializer for detecting task dependencies."""
    task_description = serializers.CharField(max_length=5000)
    existing_tasks = serializers.ListField(
        child=serializers.CharField(max_length=500),
        default=list
    )


class TaskAITagsSerializer(serializers.Serializer):
    """Serializer for generating task tags."""
    task_description = serializers.CharField(max_length=5000)
    max_tags = serializers.IntegerField(default=5, min_value=1, max_value=10)


class TaskAIStatusUpdateSerializer(serializers.Serializer):
    """Serializer for drafting status updates."""
    task_title = serializers.CharField(max_length=255)
    recent_activities = serializers.ListField(
        child=serializers.CharField(max_length=1000),
        min_length=1
    )
    target_audience = serializers.CharField(max_length=100, default="project manager")


# --- Meeting AI Serializers ---

class MeetingTranscribeSerializer(serializers.Serializer):
    """Serializer for meeting transcript processing."""
    transcript = serializers.CharField(max_length=50000)
    auto_create_tasks = serializers.BooleanField(default=False)
    project_id = serializers.UUIDField(required=False, allow_null=True)


class MeetingEmailSerializer(serializers.Serializer):
    """Serializer for drafting follow-up emails."""
    meeting_summary = serializers.CharField(max_length=10000)
    attendees = serializers.ListField(
        child=serializers.CharField(max_length=255)
    )
    sender = serializers.CharField(max_length=255)
    include_action_items = serializers.BooleanField(default=True)


# --- Code AI Serializers ---

class CodeAIReviewSerializer(serializers.Serializer):
    """Serializer for code review."""
    code = serializers.CharField(max_length=50000)
    language = serializers.CharField(max_length=50)


class CodeAIGenerateSerializer(serializers.Serializer):
    """Serializer for code generation."""
    description = serializers.CharField(max_length=5000)
    language = serializers.CharField(max_length=50)


class CodeAIExplainSerializer(serializers.Serializer):
    """Serializer for code explanation."""
    code = serializers.CharField(max_length=10000)
    language = serializers.CharField(max_length=50)


class CodeAIDebugSerializer(serializers.Serializer):
    """Serializer for debugging code."""
    code = serializers.CharField(max_length=10000)
    error_message = serializers.CharField(max_length=5000)


class CodeAITestsSerializer(serializers.Serializer):
    """Serializer for generating tests."""
    code = serializers.CharField(max_length=10000)
    language = serializers.CharField(max_length=50)


class CodeAIRefactorSerializer(serializers.Serializer):
    """Serializer for refactoring code."""
    code = serializers.CharField(max_length=10000)
    language = serializers.CharField(max_length=50)
    refactor_goal = serializers.CharField(max_length=500, default="improve readability")


class CodeAIConvertSerializer(serializers.Serializer):
    """Serializer for converting code between languages."""
    code = serializers.CharField(max_length=10000)
    from_language = serializers.CharField(max_length=50)
    to_language = serializers.CharField(max_length=50)


# --- Analytics & Assistant Serializers ---

class AnalyticsForecastSerializer(serializers.Serializer):
    """Serializer for analytics forecasting."""
    project_id = serializers.UUIDField(required=False, allow_null=True)
    confidence_level = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        default='medium'
    )


class AssistantChatSerializer(serializers.Serializer):
    """Serializer for AI assistant chat."""
    message = serializers.CharField(max_length=2000)
    context = serializers.JSONField(required=False)
    conversation_history = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        default=list
    )
    use_pro_model = serializers.BooleanField(default=False)