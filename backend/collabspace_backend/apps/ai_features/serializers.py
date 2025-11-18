from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Base Serializers ---

class ResponseSerializer(BaseModel):
    """Base class for all successful JSON responses."""
    success: bool = Field(True, description="Indicates if the operation was successful.")
    message: str = Field(..., description="A short status message.")
    data: Any = Field(None, description="The payload containing the result of the AI operation.")

# --- Task AI Serializers ---

class TaskInputSerializer(BaseModel):
    """Base input for Task AI operations."""
    content: str = Field(..., description="The text or document content to process.")
    context_id: Optional[str] = Field(None, description="ID of the project or document context.")
    
class SummarizeTaskInputSerializer(TaskInputSerializer):
    length: str = Field("medium", description="Desired length of summary (short, medium, long).")

class BreakdownOutputSerializer(BaseModel):
    subtasks: List[Dict[str, Any]] = Field(..., description="A list of generated subtasks with details.")

class BreakdownTaskOutputSerializer(ResponseSerializer):
    data: BreakdownOutputSerializer

# --- Meeting AI Serializers ---

class MeetingInputSerializer(BaseModel):
    """Base input for Meeting AI operations."""
    meeting_id: str = Field(..., description="The ID of the meeting record.")

class MeetingTranscriptionInputSerializer(MeetingInputSerializer):
    audio_file_path: str = Field(..., description="Local path or URL to the audio file.")

class MeetingSummaryOutputSerializer(BaseModel):
    summary: str
    action_items: List[str]
    attendees: List[str]

class MeetingSummaryOutput(ResponseSerializer):
    data: MeetingSummaryOutputSerializer

# --- Code AI Serializers ---

class CodeInputSerializer(BaseModel):
    file_path: str = Field(..., description="The name or path of the file being processed.")
    code: str = Field(..., description="The code content to review, explain, or generate from.")

class CodeReviewOutputSerializer(BaseModel):
    rating: int = Field(..., description="A score from 1-10 on code quality.")
    feedback: List[Dict[str, str]] = Field(..., description="List of structured suggestions (line_no, comment).")

class CodeReviewOutput(ResponseSerializer):
    data: CodeReviewOutputSerializer

# --- Analytics AI Serializers ---

class AnalyticsOutputSerializer(BaseModel):
    """Base output for long-running analytics."""
    status: str = Field(..., description="Status of the analysis job (pending, running, complete).")
    job_id: str = Field(..., description="ID of the Celery job for tracking.")

class AnalyticsJobCreated(ResponseSerializer):
    data: AnalyticsOutputSerializer

class ProjectForecastData(BaseModel):
    completion_date: str = Field(..., description="Forecasted date of project completion.")
    confidence_level: float = Field(..., description="Confidence level (0.0 to 1.0) of the forecast.")
    risk_factors: List[str]

class ProjectForecastOutput(ResponseSerializer):
    data: ProjectForecastData

# --- Assistant AI Serializers ---

class ChatInputSerializer(BaseModel):
    """Input for the conversational assistant."""
    session_id: str = Field(..., description="ID of the ongoing chat session.")
    message: str = Field(..., description="The new user message.")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Recent message history.")

class ChatOutputSerializer(BaseModel):
    response: str = Field(..., description="The AI's text response.")
    tool_used: Optional[str] = Field(None, description="The name of any tool/function the AI used.")

class ChatResponse(ResponseSerializer):
    data: ChatOutputSerializer