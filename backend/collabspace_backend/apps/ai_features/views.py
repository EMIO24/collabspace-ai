import uuid
import logging
from typing import Dict, Any

# Mock imports for Django/DRF context
class APIView:
    pass
class Response:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status
        
def status_codes():
    class Status:
        HTTP_200_OK = 200
        HTTP_201_CREATED = 201
        HTTP_400_BAD_REQUEST = 400
        HTTP_403_FORBIDDEN = 403
        HTTP_404_NOT_FOUND = 404
        HTTP_500_INTERNAL_SERVER_ERROR = 500
    return Status()
status = status_codes()

# Local imports
from .permissions import HasAIAccess
from .tasks import summarize_document_task, code_review_task, analyze_project_forecast_task, transcribe_audio_task # NEW IMPORT
from .tasks import GEMINI_PROVIDER
from .serializers import (
    SummarizeTaskInputSerializer, CodeInputSerializer, ChatInputSerializer,
    AnalyticsJobCreated, ResponseSerializer, ChatResponse, ProjectForecastOutput,
    MeetingTranscriptionInputSerializer # NEW IMPORT
)

class AIServiceFactory:
    """Mock factory focused on providing a Gemini Chat service."""
    @staticmethod
    def get_chat_service(user):
        class MockGeminiChatService:
            def chat(self, session_id, message, history):
                # Placeholder for synchronous chat call using the Gemini SDK
                return {"response": f"Gemini responded to '{message[:20]}...' on {user.plan_type} plan.", "tool_used": None}
        return MockGeminiChatService()

logger = logging.getLogger(__name__)


class BaseAIView(APIView):
    """Base class to handle common logic like permission checking."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check rate limits before processing any request."""
        # Mocking request.user for demonstration
        class MockUser:
            def __init__(self):
                self.id = "mock-user-123"
                self.plan_type = "PRO" 
            
        request.user = MockUser() 
        
        has_access, limit = HasAIAccess.has_permission(request, self)
        if not has_access:
            return Response(
                data=ResponseSerializer(
                    success=False, 
                    message=f"Daily AI usage limit ({limit}) exceeded for your plan.",
                    data={"limit": limit}
                ).model_dump(),
                status=status.HTTP_403_FORBIDDEN
            )
        return super().dispatch(request, *args, **kwargs)

    def validate_serializer(self, Serializer, data):
        """Simple Pydantic-style validation wrapper."""
        try:
            return Serializer(**data)
        except Exception as e:
            raise ValueError(f"Invalid input data: {e}")


class TaskAIView(BaseAIView):
    """Endpoints for AI operations on documents and tasks."""
    
    def post_summarize(self, request):
        """POST /api/ai/tasks/summarize/"""
        try:
            validated_data = self.validate_serializer(SummarizeTaskInputSerializer, request.data)
            job_id = str(uuid.uuid4())
            
            summarize_document_task.delay(
                job_id, 
                validated_data.content, 
                request.user.id,
                validated_data.length
            )
            
            return Response(
                data=AnalyticsJobCreated(
                    success=True, 
                    message="Summarization job started.", 
                    data={"status": "pending", "job_id": job_id}
                ).model_dump(), 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post_autocreate(self, request):
        """POST /api/ai/tasks/auto-create/"""
        return Response({"message": "Task auto-create job started."})

    def post_breakdown(self, request):
        """POST /api/ai/tasks/breakdown/"""
        return Response({"message": "Task breakdown job started."})

    def post_estimate(self, request):
        """POST /api/ai/tasks/estimate/"""
        return Response({"message": "Task estimation job started."})

    def post_priority(self, request):
        """POST /api/ai/tasks/priority/"""
        return Response({"message": "Task priority job started."})


class MeetingAIView(BaseAIView):
    """Endpoints for AI operations on meetings and transcripts."""
    
    def post_transcribe(self, request):
        """POST /api/ai/meetings/transcribe/ - NOW IMPLEMENTED"""
        try:
            # Validate input data, requiring meeting_id and audio_file_path
            validated_data = self.validate_serializer(MeetingTranscriptionInputSerializer, request.data)
            job_id = str(uuid.uuid4())
            
            # Delegate to the asynchronous transcription task
            transcribe_audio_task.delay(
                job_id, 
                validated_data.meeting_id, 
                validated_data.audio_file_path
            )
            
            return Response(
                data=AnalyticsJobCreated(
                    success=True, 
                    message="Transcription job started successfully.", 
                    data={"status": "pending", "job_id": job_id}
                ).model_dump(), 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def post_summarize(self, request):
        """POST /api/ai/meetings/summarize/"""
        return Response({"message": "Meeting summarization job started."})

    def post_action_items(self, request):
        """POST /api/ai/meetings/action-items/"""
        return Response({"message": "Action item extraction job started."})


class CodeAIView(BaseAIView):
    """Endpoints for AI operations on code."""

    def post_review(self, request):
        """POST /api/ai/code/review/"""
        try:
            validated_data = self.validate_serializer(CodeInputSerializer, request.data)
            job_id = str(uuid.uuid4())
            
            code_review_task.delay(
                job_id, 
                validated_data.code, 
                request.user.id,
                validated_data.file_path
            )

            return Response(
                data=AnalyticsJobCreated(
                    success=True, 
                    message="Code review job started.", 
                    data={"status": "pending", "job_id": job_id}
                ).model_dump(), 
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post_generate(self, request):
        """POST /api/ai/code/generate/"""
        return Response({"message": "Code generation job started."})

    def post_explain(self, request):
        """POST /api/ai/code/explain/"""
        return Response({"message": "Code explanation job started."})


class AnalyticsAIView(BaseAIView):
    """Endpoints for project analytics using AI."""

    def get_project_forecast(self, request, id: str):
        """GET /api/ai/analytics/project-forecast/{id}/"""
        
        job_id = str(uuid.uuid4())
        analyze_project_forecast_task.delay(job_id, id, request.user.id)

        if id == "sample-ready":
             return Response(
                data=ProjectForecastOutput(
                    success=True, 
                    message="Forecast complete.", 
                    data={
                        "completion_date": "2024-12-31", 
                        "confidence_level": 0.88, 
                        "risk_factors": ["Resource bottleneck in Q4", "External dependency delay"]
                    }
                ).model_dump(),
                status=status.HTTP_200_OK
            )

        return Response(
            data=AnalyticsJobCreated(
                success=True, 
                message=f"Project forecast job started for project {id}.", 
                data={"status": "pending", "job_id": job_id}
            ).model_dump(), 
            status=status.HTTP_201_CREATED
        )

    def get_burnout_detection(self, request):
        """GET /api/ai/analytics/burnout-detection/"""
        return Response({"message": "Burnout detection job started."})

    def get_velocity(self, request):
        """GET /api/ai/analytics/velocity/"""
        return Response({"message": "Velocity analysis job started."})


class AssistantView(BaseAIView):
    """Endpoints for the conversational AI assistant."""
    
    def post_chat(self, request):
        """POST /api/ai/assistant/chat/"""
        try:
            validated_data = self.validate_serializer(ChatInputSerializer, request.data)
            
            service = AIServiceFactory.get_chat_service(request.user)
            result = service.chat(
                validated_data.session_id, 
                validated_data.message, 
                validated_data.history
            )
            
            return Response(
                data=ChatResponse(
                    success=True, 
                    message="Chat response generated.", 
                    data={
                        "response": result['response'], 
                        "tool_used": result.get('tool_used')
                    }
                ).model_dump(),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return Response({"error": "Failed to get chat response."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post_search(self, request):
        """POST /api/ai/assistant/search/"""
        return Response({"message": "Assistant search initiated."})