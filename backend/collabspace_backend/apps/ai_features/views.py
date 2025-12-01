from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from django.db.models import Q

# Local Imports
from .permissions import HasAIAccess, HasAIQuota, CanUseAdvancedAI, CanManageAITemplates
from .services.task_ai import TaskAIService
from .services.meeting_ai import MeetingAIService
from .services.analytics_ai import AnalyticsAIService
from .services.gemini_service import GeminiService
from .models import AIUsage, AIPromptTemplate, AIRateLimit, AICache
from .serializers import *

from apps.workspaces.models import Workspace


# --- Mixin for AI Views ---

class AIViewMixin:
    """Handles common AI error and permission responses."""
    
    permission_classes = [HasAIAccess, HasAIQuota]
    
    def handle_ai_call(self, service_method, serializer_class, *args, **kwargs):
        """Standardizes request validation, service call, and error handling."""
        
        print(f"DEBUG: handle_ai_call started for user: {self.request.user.email}")
        print(f"DEBUG: Request data: {self.request.data}")
        
        # 1. Validation
        serializer = serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        print(f"DEBUG: Serializer validated, data: {validated_data}")
        
        user = self.request.user
        
        # 2. Get workspace from request data or user's default workspace
        workspace_id = self.request.data.get('workspace_id')
        
        print(f"DEBUG: workspace_id from request: {workspace_id}")
        
        if workspace_id:
            try:
                # Try to get workspace by ID first
                workspace = Workspace.objects.filter(id=workspace_id).first()
                
                if not workspace:
                    return Response({
                        'error': 'INVALID_WORKSPACE',
                        'message': 'Workspace not found.'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Check if user has access (either owner or active member)
                is_owner = workspace.owner == user
                is_member = workspace.members.filter(user=user, is_active=True).exists()
                
                print(f"DEBUG: Workspace found: {workspace.id}, is_owner: {is_owner}, is_member: {is_member}")
                
                if not (is_owner or is_member):
                    return Response({
                        'error': 'INVALID_WORKSPACE',
                        'message': 'You do not have access to this workspace.'
                    }, status=status.HTTP_403_FORBIDDEN)
                    
            except Exception as e:
                import traceback
                print(f"ERROR getting workspace: {e}")
                traceback.print_exc()
                return Response({
                    'error': 'WORKSPACE_ERROR',
                    'message': f'Error retrieving workspace: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Get user's first workspace (check owned first, then memberships)
            print(f"DEBUG: Looking for workspace for user {user.email}")
            workspace = Workspace.objects.filter(owner=user).first()
            print(f"DEBUG: Owned workspace: {workspace}")
            
            if not workspace:
                # Check if user is a member of any workspace
                print(f"DEBUG: Checking memberships...")
                membership = user.workspace_memberships.filter(is_active=True).select_related('workspace').first()
                print(f"DEBUG: Found membership: {membership}")
                if membership:
                    workspace = membership.workspace
                    print(f"DEBUG: Workspace from membership: {workspace}")
            
            if not workspace:
                return Response({
                    'error': 'NO_WORKSPACE',
                    'message': 'No workspace found. Please provide a workspace_id.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"DEBUG: Final workspace: {workspace}")
        
        try:
            # 3. Service Call - Pass workspace as second parameter
            print(f"DEBUG AIViewMixin: Calling service method with user={user.username}, workspace={workspace.id}, validated_data={validated_data}")
            
            # Note: validated_data is unpacked as **kwargs into service_method
            result = service_method(user, workspace, *args, **validated_data, **kwargs)
            
            print(f"DEBUG AIViewMixin: Service call succeeded, result keys: {result.keys() if isinstance(result, dict) else type(result)}")
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log the full exception for debugging
            print(f"ERROR in AIViewMixin.handle_ai_call: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if it's an API-related error (from Google AI SDK)
            error_str = str(e)
            if any(x in error_str.lower() for x in ['api', 'quota', 'rate limit', 'safety', 'blocked']):
                return Response({
                    'error': 'AI_API_ERROR', 
                    'message': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # 4. General Server Error (e.g., internal service error, DB error)
            return Response({
                'error': 'INTERNAL_ERROR', 
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- API Views ---

class TaskAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Task AI features (summarization, breakdown, etc.)."""
    
    service = TaskAIService()
    
    @action(detail=False, methods=['post'], serializer_class=TaskAISummarizeSerializer)
    def summarize(self, request):
        # Service method wrapper isn't strictly needed if arguments match exactly, 
        # but safe to define if you want explicit control.
        # TaskAIService.summarize_task(user, workspace, task_id=None, task_text=None)
        return self.handle_ai_call(self.service.summarize_task, TaskAISummarizeSerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAICreateSerializer)
    def auto_create(self, request):
        def service_wrapper(user, workspace, text, workspace_id=None, project_id=None, **kwargs):
            # Added **kwargs to safely ignore extra fields
            tasks = self.service.auto_create_from_text(user, workspace, text, use_pro=True)
            return {'created_tasks': tasks}
            
        return self.handle_ai_call(service_wrapper, TaskAICreateSerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAIBreakdownSerializer)
    def breakdown(self, request):
        # FIX: Updated wrapper to accept ALL serializer fields explicitly
        def service_wrapper(user, workspace, task_description, num_subtasks=5, auto_create=False, **kwargs):
            subtasks = self.service.break_down_task(
                user, 
                workspace,
                task_description, 
                num_subtasks=num_subtasks, 
                use_pro=CanUseAdvancedAI().has_permission(request, self)
            )
            if auto_create:
                # Logic to actually create subtasks in DB would go here
                pass 
            return {'subtasks': subtasks}
            
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
        def service_wrapper(user, workspace, transcript, **kwargs):
            return self.service.summarize_meeting(user, workspace, transcript)
            
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)

    @action(detail=False, methods=['post'], serializer_class=MeetingTranscribeSerializer)
    def action_items(self, request):
        def service_wrapper(user, workspace, transcript, auto_create_tasks=False, project_id=None, **kwargs):
            items = self.service.extract_action_items(
                user, 
                workspace,
                transcript, 
                use_pro=CanUseAdvancedAI().has_permission(request, self)
            )
            if auto_create_tasks:
                pass
            return {'action_items': items}
            
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)

    @action(detail=False, methods=['post'], serializer_class=MeetingTranscribeSerializer)
    def sentiment(self, request):
        def service_wrapper(user, workspace, transcript, **kwargs):
            return self.service.analyze_sentiment(user, workspace, transcript)
            
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)


class AnalyticsAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Analytics AI features (forecasting, optimization, etc.)."""
    
    service = AnalyticsAIService()
    permission_classes = [HasAIAccess, HasAIQuota, CanUseAdvancedAI]

    def _get_dummy_project_data(self, project_id):
        return f"Project ID {project_id} data: Velocity=20, Scope=300 points, Team=5, Risk=Medium."
    
    @action(detail=True, methods=['get'])
    def project_forecast(self, request, pk=None):
        project_data = self._get_dummy_project_data(pk)
        
        def service_wrapper(user, workspace, **kwargs):
            return self.service.forecast_completion(user, workspace, project_data=project_data)
        
        return self.handle_ai_call(service_wrapper, AnalyticsForecastSerializer)

    @action(detail=True, methods=['get'])
    def burnout_detection(self, request, pk=None):
        team_data = self._get_dummy_project_data(pk)
        
        def service_wrapper(user, workspace, **kwargs):
            return self.service.detect_burnout_risk(user, workspace, team_data=team_data)
        
        return self.handle_ai_call(service_wrapper, AnalyticsForecastSerializer)

    @action(detail=True, methods=['get'])
    def velocity(self, request, pk=None):
        sprint_data = self._get_dummy_project_data(pk)
        
        def service_wrapper(user, workspace, **kwargs):
            return self.service.analyze_velocity(user, workspace, sprint_data=sprint_data, use_pro=False)
        
        return self.handle_ai_call(service_wrapper, AnalyticsForecastSerializer)

    @action(detail=False, methods=['post'])
    def resource_optimizer(self, request):
        workspace_data = self._get_dummy_project_data(request.data.get('workspace_id', 'dummy'))
        
        def service_wrapper(user, workspace, **kwargs):
            return self.service.suggest_resource_allocation(user, workspace, workspace_data=workspace_data)
        
        return self.handle_ai_call(service_wrapper, AnalyticsForecastSerializer)

    @action(detail=True, methods=['get'])
    def bottlenecks(self, request, pk=None):
        workflow_data = self._get_dummy_project_data(pk)
        
        def service_wrapper(user, workspace, **kwargs):
            return self.service.identify_bottlenecks(user, workspace, workflow_data=workflow_data)
        
        return self.handle_ai_call(service_wrapper, AnalyticsForecastSerializer)


class AssistantView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for general AI assistant/chat functionality."""
    
    service = GeminiService()
    
    @action(detail=False, methods=['post'], serializer_class=AssistantChatSerializer)
    def chat(self, request):
        # Use handle_ai_call to manage validation, workspace, and error handling
        def service_wrapper(user, workspace, message, conversation_history=None, use_pro_model=False, **kwargs):
            # Build message history - handle None case
            history = conversation_history if conversation_history is not None else []
            messages = history + [{'role': 'user', 'text': message}]
            
            # Call the service
            response = self.service.generate_chat(
                user, 
                workspace,
                messages, 
                'assistant_chat', 
                use_pro=use_pro_model
            )
            
            return {
                'response': response.get('text'), 
                'tokens': response.get('total_tokens')
            }
        
        return self.handle_ai_call(service_wrapper, AssistantChatSerializer)

    @action(detail=False, methods=['post'])
    def search(self, request):
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
        
        prompt = template.prompt_template
        for key, value in sample_data.items():
            prompt = prompt.replace(f'{{{{{key}}}}}', str(value))
            
        return Response({'test_prompt': prompt, 'variables': template.variables})