from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from google.generativeai.errors import APIError

# Local Imports
from .permissions import HasAIAccess, HasAIQuota, CanUseAdvancedAI, CanManageAITemplates
from .services.task_ai import TaskAIService
from .services.meeting_ai import MeetingAIService
from .services.analytics_ai import AnalyticsAIService
from .services.gemini_service import GeminiService
from .models import AIUsage, AIPromptTemplate, AIRateLimit, AICache
from .serializers import * # Import all serializers

# --- Mixin for AI Views ---

class AIViewMixin:
    """Handles common AI error and permission responses."""
    
    permission_classes = [HasAIAccess, HasAIQuota]
    
    def handle_ai_call(self, service_method, serializer_class, *args, **kwargs):
        """Standardizes request validation, service call, and error handling."""
        
        # 1. Validation
        serializer = serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        user = self.request.user
        
        try:
            # 2. Service Call
            result = service_method(user, **validated_data, *args, **kwargs)
            return Response(result, status=status.HTTP_200_OK)
            
        except APIError as e:
            # 3. API Error Handling (e.g., final failure after retries, safety block)
            return Response({'error': 'AI_API_ERROR', 'message': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            # 4. General Server Error (e.g., internal service error, DB error)
            return Response({'error': 'INTERNAL_ERROR', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- API Views ---

class TaskAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Task AI features (summarization, breakdown, etc.)."""
    
    service = TaskAIService()
    
    @action(detail=False, methods=['post'], serializer_class=TaskAISummarizeSerializer)
    def summarize(self, request):
        return self.handle_ai_call(self.service.summarize_task, TaskAISummarizeSerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAICreateSerializer)
    def auto_create(self, request):
        # NOTE: Task creation logic (saving to DB) must happen here after the AI call
        def service_wrapper(user, text, workspace_id, project_id=None):
            tasks = self.service.auto_create_from_text(user, text, use_pro=True)
            # Placeholder: In a real app, this would call a Task model service to save the tasks
            # tasks = TaskService.create_tasks(user, workspace_id, project_id, tasks)
            return {'created_tasks': tasks}
            
        return self.handle_ai_call(service_wrapper, TaskAICreateSerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAIBreakdownSerializer)
    def breakdown(self, request):
        # Assuming task_description is passed directly for simplicity, or fetched from task_id
        task_description = request.data.get('task_description') or "Large epic task description." 
        num_subtasks = request.data.get('num_subtasks')
        auto_create = request.data.get('auto_create', False)
        
        def service_wrapper(user):
            # Pass use_pro based on user permission (if applicable)
            subtasks = self.service.break_down_task(user, task_description, num_subtasks=num_subtasks, use_pro=CanUseAdvancedAI().has_permission(request, self))
            if auto_create:
                # Placeholder: Call SubTaskService.create_subtasks(task_id, subtasks)
                pass 
            return {'subtasks': subtasks}
            
        # Use a dummy serializer for simple validation since breakdown has complex logic
        return self.handle_ai_call(service_wrapper, TaskAIBreakdownSerializer)
        
    @action(detail=False, methods=['post'], serializer_class=TaskAIEstimateSerializer)
    def estimate(self, request):
        return self.handle_ai_call(self.service.estimate_effort, TaskAIEstimateSerializer)
        
    @action(detail=False, methods=['post'], serializer_class=TaskAIPrioritySerializer)
    def priority(self, request):
        return self.handle_ai_call(self.service.suggest_priority, TaskAIPrioritySerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAIAssigneeSerializer)
    def suggest_assignee(self, request):
        return self.handle_ai_call(self.service.suggest_assignee, TaskAIAssigneeSerializer)


class MeetingAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Meeting AI features (summarization, action items, sentiment)."""
    
    service = MeetingAIService()
    
    @action(detail=False, methods=['post'], serializer_class=MeetingTranscribeSerializer)
    def summarize(self, request):
        # Use Pro model for better summarization
        def service_wrapper(user, transcript, **kwargs):
            return self.service.summarize_meeting(user, transcript)
            
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)

    @action(detail=False, methods=['post'], serializer_class=MeetingTranscribeSerializer)
    def action_items(self, request):
        def service_wrapper(user, transcript, auto_create_tasks=False, project_id=None):
            items = self.service.extract_action_items(user, transcript, use_pro=CanUseAdvancedAI().has_permission(request, self))
            if auto_create_tasks:
                # Placeholder: TaskService.create_tasks_from_action_items(project_id, items)
                pass
            return {'action_items': items}
            
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)

    @action(detail=False, methods=['post'], serializer_class=MeetingTranscribeSerializer)
    def sentiment(self, request):
        def service_wrapper(user, transcript, **kwargs):
            return self.service.analyze_sentiment(user, transcript)
            
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)


class AnalyticsAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Analytics AI features (forecasting, optimization, etc.)."""
    
    service = AnalyticsAIService()
    permission_classes = [HasAIAccess, HasAIQuota, CanUseAdvancedAI] # Analytics usually requires Pro

    def _get_dummy_project_data(self, project_id):
        # In a real app, this would query Task, Sprint, and Team models.
        return f"Project ID {project_id} data: Velocity=20, Scope=300 points, Team=5, Risk=Medium."
    
    @action(detail=True, methods=['get'])
    def project_forecast(self, request, pk=None):
        project_data = self._get_dummy_project_data(pk)
        return self.handle_ai_call(self.service.forecast_completion, AnalyticsForecastSerializer, project_data=project_data)

    @action(detail=True, methods=['get'])
    def burnout_detection(self, request, pk=None):
        team_data = self._get_dummy_project_data(pk)
        return self.handle_ai_call(self.service.detect_burnout_risk, AnalyticsForecastSerializer, team_data=team_data)

    @action(detail=True, methods=['get'])
    def velocity(self, request, pk=None):
        sprint_data = self._get_dummy_project_data(pk)
        return self.handle_ai_call(self.service.analyze_velocity, AnalyticsForecastSerializer, sprint_data=sprint_data, use_pro=False)

    @action(detail=False, methods=['post'])
    def resource_optimizer(self, request):
        workspace_data = self._get_dummy_project_data(request.data.get('workspace_id', 'dummy'))
        return self.handle_ai_call(self.service.suggest_resource_allocation, AnalyticsForecastSerializer, workspace_data=workspace_data)

    @action(detail=True, methods=['get'])
    def bottlenecks(self, request, pk=None):
        workflow_data = self._get_dummy_project_data(pk)
        return self.handle_ai_call(self.service.identify_bottlenecks, AnalyticsForecastSerializer, workflow_data=workflow_data)


class AssistantView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for general AI assistant/chat functionality."""
    
    service = GeminiService() # Use the base service directly for chat
    
    @action(detail=False, methods=['post'], serializer_class=AssistantChatSerializer)
    def chat(self, request):
        # The serializer handles validation
        validated_data = AssistantChatSerializer(data=request.data).is_valid(raise_exception=True)
        
        message = validated_data.get('message')
        history = validated_data.get('conversation_history', [])
        use_pro = validated_data.get('use_pro_model', False)
        
        # Format the new message and history for the chat API
        messages = history + [{'role': 'user', 'text': message}]
        
        # NOTE: This API is complex and uses raw service method directly
        try:
            response = self.service.generate_chat(request.user, messages, 'assistant_chat', use_pro=use_pro)
            return Response({'response': response.get('text'), 'tokens': response.get('total_tokens')})
        except APIError as e:
            return Response({'error': 'CHAT_API_ERROR', 'message': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['post'])
    def search(self, request):
        # This requires Gemini embeddings, a separate service, or context
        return Response({'message': 'Semantic search feature placeholder.'})

class AIUsageView(viewsets.GenericViewSet):
    """Endpoints for tracking and displaying AI usage statistics."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def usage(self, request):
        """Get current user's AI usage logs."""
        logs = AIUsage.objects.filter(user=request.user).order_by('-created_at')[:50]
        return Response(AIUsageSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'])
    def workspace_usage(self, request, pk=None):
        """Get workspace AI usage (admin only)."""
        # Placeholder: Check if user is admin of workspace PK
        # logs = AIUsage.objects.filter(workspace_id=pk).order_by('-created_at')[:50]
        return Response({'message': 'Workspace usage feature placeholder.'})

    @action(detail=False, methods=['get'])
    def quota(self, request):
        """Check remaining quota (daily and per-minute)."""
        rate_limit, _ = AIRateLimit.objects.get_or_create(user=request.user)
        return Response(AIRateLimitSerializer(rate_limit).data)


class AITemplateViewSet(viewsets.ModelViewSet):
    """CRUD for AI Prompt Templates (admin only)."""
    
    queryset = AIPromptTemplate.objects.all()
    serializer_class = AIPromptTemplateSerializer
    permission_classes = [CanManageAITemplates]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test template with sample data."""
        template = self.get_object()
        sample_data = request.data.get('sample_data', {})
        
        # Basic variable substitution
        prompt = template.prompt_template
        for key, value in sample_data.items():
            prompt = prompt.replace(f'{{{{{key}}}}}', str(value))
            
        return Response({'test_prompt': prompt, 'variables': template.variables})