import json
import os # Added for potential file handling/cleanup
from typing import List, Dict, Any, Optional
from pydantic import BaseModel as PydanticBaseModel, Field

# Local imports
from .gemini_service import GeminiService
from .audio_service import AudioService # Assumed new module/service
from ..models import AIRateLimit 


class TaskAIService:
    """
    Service class responsible for all AI-powered task functionalities using the Gemini model.
    It leverages structured output (via Pydantic schemas) for reliable data extraction.
    """
    
    FEATURE_TYPE = 'task_ai' 
    
    def __init__(self, user: Optional[User] = None):
        """Initializes the TaskAIService with the Gemini client, user context, and audio service."""
        self.user = user or User(id=999, email="default_ai_user@collabspace.com")
        self.ai = GeminiService()
        self.audio_processor = AudioService() # New service initialization


    def create_task_from_audio(self, audio_file_path: str, use_pro: bool = False) -> List[Dict[str, Any]]:
        """
        Transcribes an audio file and uses the resulting text to create structured tasks.
        """
        print(f"Starting STT for file: {audio_file_path}")
        
        # 1. Transcribe the audio file using the external service
        try:
            transcript = self.audio_processor.transcribe(audio_file_path)
            if not transcript:
                return [{"title": "Error: Empty Transcript", "description": "Audio transcription failed or resulted in empty text.", "priority": "low"}]
        except Exception as e:
            print(f"Audio transcription error: {e}")
            return [{"title": "Error: Transcription Failed", "description": str(e), "priority": "medium"}]
        
        print(f"Transcription successful. Text length: {len(transcript)}")

        return self.auto_create_from_text(text=transcript, use_pro=use_pro)

    def auto_create_from_text(self, text: str, use_pro: bool = False) -> List[Dict[str, Any]]:
        """Parses a block of natural language text and extracts structured tasks."""
        
        # ... (implementation remains the same) ...
        
        prompt = f"""
                    Analyze the following natural language text and extract all actionable tasks. 
                    Text: "{text}"

                    For each extracted task, provide a title, a detailed description, and a suggested priority (low, medium, high, or urgent).
                    Return the result as a JSON array that strictly adheres to the provided schema for Task.
                """
        try:
            # Enforce structured output
            json_array = self.ai.generate_structured_json(
                prompt, 
                user=self.user, 
                feature_type=self.FEATURE_TYPE, 
                schema=List[Task], 
                use_pro=use_pro
            )
            return json_array
        except Exception as e:
            print(f"Warning: Task extraction failed: {e}")
            return [{"title": "Error: Task Extraction Failed", "description": str(e), "priority": "medium"}]

class SubTask(PydanticBaseModel):
    title: str = Field(description="The concise title for the subtask.")
    description: str = Field(description="The detailed steps for the subtask.")
    estimated_hours: int = Field(description="The estimated effort in hours (integer).")

class Task(PydanticBaseModel):
    title: str = Field(description="The extracted title for the task.")
    description: str = Field(description="The extracted detailed description for the task.")
    priority: str = Field(description="The suggested priority (low, medium, high, urgent).")


class TaskAIService:
    """Service class for all AI-powered task functionalities."""
    
    FEATURE_TYPE = 'task_ai'

    def __init__(self):
        self.ai = GeminiService()

    def summarize_task(self, user, task_description: str) -> str:
        """Generate concise task summary."""
        prompt = f"Generate a concise, single-sentence summary for the following task description: {task_description}"
        response = self.ai.generate_completion(user, prompt, self.FEATURE_TYPE, max_tokens=100)
        return response.get('text', 'Failed to generate summary.')

    def break_down_task(self, user, task_description: str, num_subtasks: int = 5, use_pro: bool = False) -> List[Dict[str, Any]]:
        """Break epic task into structured subtasks."""
        prompt = f"Break down the following epic task into 3 to {num_subtasks} highly detailed subtasks. Task: {task_description}"
        return self.ai.generate_structured_json(user, prompt, self.FEATURE_TYPE, schema=List[SubTask], use_pro=use_pro)

    def estimate_effort(self, user, task_description: str, project_context: Optional[str] = None) -> str:
        """Estimate task effort in hours, providing justification."""
        context = f"Project Context: {project_context}\n" if project_context else ""
        prompt = f"{context} Estimate the effort for the task: {task_description}. Return only the final estimate and justification in the format: 'Estimate: X hours. Justification: [Your justification].'"
        response = self.ai.generate_completion(user, prompt, self.FEATURE_TYPE, max_tokens=200, temperature=0.5)
        return response.get('text', 'Failed to generate estimate.')

    def suggest_priority(self, user, task_description: str, due_date: Optional[str] = None) -> str:
        """Suggest task priority (CRITICAL/HIGH/MEDIUM/LOW)."""
        date_str = f"The due date is {due_date}. " if due_date else ""
        prompt = f"Based on the task: {task_description} and date: {date_str}, suggest the priority level. Choose one from 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'. Return ONLY the word."
        response = self.ai.generate_completion(user, prompt, self.FEATURE_TYPE, max_tokens=10)
        return response.get('text', 'MEDIUM').strip().upper()

    def detect_dependencies(self, user, task_description: str, existing_tasks: List[str]) -> List[str]:
        """Detect potential task dependencies (returns list of task descriptions)."""
        tasks_list = "\n- ".join(existing_tasks)
        prompt = f"New task: '{task_description}'. Identify which existing tasks it depends on. Existing Tasks:\n- {tasks_list}. Return a JSON array of the dependent task descriptions."
        
        # Use completion and parse manually for a list of strings
        response = self.ai.generate_completion(user, prompt, self.FEATURE_TYPE, max_tokens=1000)
        try:
            return json.loads(response.get('text', '[]'))
        except json.JSONDecodeError:
            return []

    def suggest_assignee(self, user, task_description: str, team_members: List[Dict[str, str]]) -> str:
        """Suggest best assignee based on skills (returns name)."""
        member_list = "\n- ".join([f"{m['name']} (Skills: {m.get('skills', 'None listed')})" for m in team_members])
        prompt = f"Based on task: {task_description} and team: {member_list}, suggest the most suitable assignee. Return ONLY the name of the suggested person."
        response = self.ai.generate_completion(user, prompt, self.FEATURE_TYPE, max_tokens=20)
        
        suggested_name = response.get('text', '').strip()
        # Basic validation
        if suggested_name in [m['name'] for m in team_members]:
            return suggested_name
        return "Unassigned"

    # --- EXTRA FUNCTIONS ADDED BELOW ---

    def generate_task_tags(self, user, task_description: str, max_tags: int = 5) -> List[str]:
        """
        Generates relevant keywords/tags for a task to aid in searching and filtering.
        """
        prompt = (
            f"Analyze the following task description and generate up to {max_tags} concise, single-word, "
            f"lowercase tags/keywords that accurately categorize the task's content. "
            f"Task: '{task_description}'. Return a JSON array of strings (e.g., [\"backend\", \"security\"])."
        )
        response = self.ai.generate_completion(user, prompt, self.FEATURE_TYPE, max_tokens=50)
        try:
            # The AI is instructed to return a JSON array, so we parse the text
            return json.loads(response.get('text', '[]'))
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse tag JSON: {response.get('text')}")
            return []

    def draft_status_update(self, user, task_title: str, recent_activities: List[str], target_audience: str = "project manager") -> str:
        """
        Drafts a brief, professional status update based on recent activities.
        """
        activities_list = "\n- ".join(recent_activities)
        prompt = (
            f"Draft a professional, concise (2-3 sentences max) status update about the task '{task_title}' "
            f"for a '{target_audience}'. "
            f"Summarize the following recent activities into the update:\n- {activities_list}. "
            f"Focus on progress, blockers, and next steps."
        )
        response = self.ai.generate_completion(user, prompt, self.FEATURE_TYPE, max_tokens=300, temperature=0.6)
        return response.get('text', 'Failed to draft status update.')