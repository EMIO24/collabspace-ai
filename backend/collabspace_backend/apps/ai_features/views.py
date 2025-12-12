import uuid
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
from .services.code_ai import CodeAIService
from .services.gemini_service import GeminiService
from .models import AIUsage, AIPromptTemplate, AIRateLimit, AICache
from .serializers import *

from apps.workspaces.models import Workspace
from apps.tasks.models import Task 


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
        
        # 2. Get workspace
        workspace_id = self.request.data.get('workspace_id') or self.request.query_params.get('workspace_id')
        
        if workspace_id:
            try:
                workspace = Workspace.objects.filter(id=workspace_id).first()
                if not workspace:
                    return Response({'error': 'INVALID_WORKSPACE', 'message': 'Workspace not found.'}, status=status.HTTP_404_NOT_FOUND)
                
                # Check access
                is_owner = workspace.owner == user
                is_member = workspace.members.filter(user=user, is_active=True).exists()
                
                if not (is_owner or is_member):
                    return Response({'error': 'INVALID_WORKSPACE', 'message': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
                    
            except Exception as e:
                return Response({'error': 'WORKSPACE_ERROR', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Fallback to first workspace
            workspace = Workspace.objects.filter(owner=user).first()
            if not workspace:
                membership = user.workspace_memberships.filter(is_active=True).first()
                if membership: workspace = membership.workspace
            
            if not workspace:
                return Response({'error': 'NO_WORKSPACE', 'message': 'No workspace found.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 3. Service Call
            result = service_method(user, workspace, *args, **validated_data, **kwargs)
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': 'AI_ERROR', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- API Views ---

class TaskAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Task AI features."""
    
    service = TaskAIService()
    
    @action(detail=False, methods=['post'], serializer_class=TaskAISummarizeSerializer)
    def summarize(self, request):
        return self.handle_ai_call(self.service.summarize_task, TaskAISummarizeSerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAICreateSerializer)
    def auto_create(self, request):
        def service_wrapper(user, workspace, text, workspace_id=None, project_id=None, **kwargs):
            # 1. Generate task data from AI
            print(f"DEBUG: Generating tasks for text: '{text[:20]}...'")
            generated_data = self.service.auto_create_from_text(user, workspace, text, use_pro=True)
            print(f"DEBUG: Generated Data Count: {len(generated_data) if generated_data else 0}")
            
            created_tasks = []
            
            # 2. If project_id provided, actually create the tasks in DB
            if project_id and isinstance(generated_data, list):
                print(f"DEBUG: Saving to Project ID: {project_id}")
                for task_item in generated_data:
                    title = task_item.get('title')
                    if not title: continue
                    
                    try:
                        task = Task.objects.create(
                            title=title[:255],
                            description=task_item.get('description', ''),
                            priority=task_item.get('priority', 'medium').lower(),
                            status='todo',
                            project_id=project_id,
                            created_by=user
                        )
                        task_item['id'] = str(task.id)
                        task_item['status'] = 'created'
                        created_tasks.append(task_item)
                        print(f"DEBUG: Created task {task.id}")
                    except Exception as e:
                        print(f"ERROR: Failed to save task '{title}': {e}")
                        task_item['status'] = 'failed'
                        task_item['error'] = str(e)
                        created_tasks.append(task_item)
                
                return {'created_tasks': created_tasks}
            else:
                print("DEBUG: Skipping DB creation (no project_id or invalid data)")
            
            return {'suggested_tasks': generated_data}
            
        return self.handle_ai_call(service_wrapper, TaskAICreateSerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAIBreakdownSerializer)
    def breakdown(self, request):
        def service_wrapper(user, workspace, task_description=None, task_id=None, num_subtasks=5, auto_create=False, **kwargs):
            description = task_description
            
            if not description and task_id:
                 try:
                     task_obj = Task.objects.get(id=task_id)
                     description = task_obj.description or task_obj.title
                 except Task.DoesNotExist:
                     pass

            subtasks = self.service.break_down_task(
                user, 
                workspace,
                task_description=description or "Task breakdown",
                num_subtasks=num_subtasks, 
                use_pro=CanUseAdvancedAI().has_permission(request, self)
            )
            
            if task_id:
                try:
                    task_obj = Task.objects.get(id=task_id)
                    current_subtasks = task_obj.subtasks or []
                    if not isinstance(current_subtasks, list): current_subtasks = []

                    new_subtasks_formatted = []
                    for st in subtasks:
                        new_subtasks_formatted.append({
                            'id': str(uuid.uuid4()),
                            'title': st.get('title'),
                            'completed': False
                        })
                    
                    task_obj.subtasks = current_subtasks + new_subtasks_formatted
                    task_obj.save()
                except Exception as e:
                    print(f"Failed to save breakdown to task: {e}")
                
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

    @action(detail=False, methods=['post'], serializer_class=TaskAIDependencySerializer)
    def dependencies(self, request):
        def service_wrapper(user, workspace, task_description, existing_tasks=[], **kwargs):
            return {'dependencies': self.service.detect_dependencies(user, workspace, task_description, existing_tasks)}
        return self.handle_ai_call(service_wrapper, TaskAIDependencySerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAITagsSerializer)
    def tags(self, request):
        def service_wrapper(user, workspace, task_description, max_tags=5, **kwargs):
            return {'tags': self.service.generate_task_tags(user, workspace, task_description, max_tags)}
        return self.handle_ai_call(service_wrapper, TaskAITagsSerializer)

    @action(detail=False, methods=['post'], serializer_class=TaskAIStatusUpdateSerializer)
    def status_update(self, request):
        def service_wrapper(user, workspace, task_title, recent_activities, target_audience="manager", **kwargs):
            return {'update_draft': self.service.draft_status_update(user, workspace, task_title, recent_activities, target_audience)}
        return self.handle_ai_call(service_wrapper, TaskAIStatusUpdateSerializer)


class MeetingAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Meeting AI features."""
    
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
            return {'action_items': items}
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)

    @action(detail=False, methods=['post'], serializer_class=MeetingTranscribeSerializer)
    def sentiment(self, request):
        def service_wrapper(user, workspace, transcript, **kwargs):
            return self.service.analyze_sentiment(user, workspace, transcript)
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)
    
    @action(detail=False, methods=['post'], serializer_class=MeetingTranscribeSerializer)
    def decisions(self, request):
        def service_wrapper(user, workspace, transcript, **kwargs):
            return self.service.extract_decisions(user, workspace, transcript)
        return self.handle_ai_call(service_wrapper, MeetingTranscribeSerializer)

    @action(detail=False, methods=['post'], serializer_class=MeetingEmailSerializer)
    def follow_up_email(self, request):
        def service_wrapper(user, workspace, meeting_summary, attendees, sender, include_action_items=True, **kwargs):
            return self.service.draft_follow_up_email(user, workspace, meeting_summary, attendees, sender, include_action_items)
        return self.handle_ai_call(service_wrapper, MeetingEmailSerializer)


class CodeAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Code AI features."""
    
    service = CodeAIService()
    permission_classes = [HasAIAccess, HasAIQuota, CanUseAdvancedAI]

    @action(detail=False, methods=['post'], serializer_class=CodeAIReviewSerializer)
    def review(self, request):
        def service_wrapper(user, workspace, code, language, **kwargs):
            return self.service.review_code(user, workspace, code, language)
        return self.handle_ai_call(service_wrapper, CodeAIReviewSerializer)

    @action(detail=False, methods=['post'], serializer_class=CodeAIGenerateSerializer)
    def generate(self, request):
        def service_wrapper(user, workspace, description, language, **kwargs):
            return self.service.generate_code(user, workspace, description, language)
        return self.handle_ai_call(service_wrapper, CodeAIGenerateSerializer)

    @action(detail=False, methods=['post'], serializer_class=CodeAIExplainSerializer)
    def explain(self, request):
        def service_wrapper(user, workspace, code, language, **kwargs):
            return self.service.explain_code(user, workspace, code, language)
        return self.handle_ai_call(service_wrapper, CodeAIExplainSerializer)

    @action(detail=False, methods=['post'], serializer_class=CodeAIDebugSerializer)
    def debug(self, request):
        def service_wrapper(user, workspace, code, error_message, **kwargs):
            return self.service.debug_code(user, workspace, code, error_message)
        return self.handle_ai_call(service_wrapper, CodeAIDebugSerializer)

    @action(detail=False, methods=['post'], serializer_class=CodeAITestsSerializer)
    def tests(self, request):
        def service_wrapper(user, workspace, code, language, **kwargs):
            return self.service.generate_tests(user, workspace, code, language)
        return self.handle_ai_call(service_wrapper, CodeAITestsSerializer)
    
    @action(detail=False, methods=['post'], serializer_class=CodeAIRefactorSerializer)
    def refactor(self, request):
        def service_wrapper(user, workspace, code, language, refactor_goal="improve readability", **kwargs):
            return self.service.refactor_code(user, workspace, code, language, refactor_goal)
        return self.handle_ai_call(service_wrapper, CodeAIRefactorSerializer)
    
    @action(detail=False, methods=['post'], serializer_class=CodeAIConvertSerializer)
    def convert(self, request):
        def service_wrapper(user, workspace, code, from_language, to_language, **kwargs):
            return self.service.convert_code(user, workspace, code, from_language, to_language)
        return self.handle_ai_call(service_wrapper, CodeAIConvertSerializer)


class AnalyticsAIView(AIViewMixin, viewsets.GenericViewSet):
    """Endpoints for Analytics AI features."""
    
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
        def service_wrapper(user, workspace, message, conversation_history=None, use_pro_model=False, **kwargs):
            history = conversation_history if conversation_history is not None else []
            messages = history + [{'role': 'user', 'text': message}]
            
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