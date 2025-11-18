import json
from typing import List, Dict, Any, Optional

# CollabSpace Placeholder Imports and new imports
from .base_ai_service import User # Assuming the calling context provides a User object
from .openai_service import OpenAIService 
# Import the new GeminiService and Pydantic schema
from .gemini_service import GeminiService, SubTask, BaseModel, Field 


class Task(BaseModel):
    title: str = Field(description="The extracted title for the task.")
    description: str = Field(description="The extracted detailed description for the task.")
    priority: str = Field(description="The suggested priority (low, medium, high, urgent).")


class TaskAIService:
    def __init__(self, provider: str = 'openai', user: Optional[User] = None):
        # We need a user object to track usage and enforce rate limits
        self.user = user or User(id=999, email="default_ai_user@collabspace.com")
        
        if provider == 'openai':
            self.ai = OpenAIService()
        elif provider == 'gemini': # New provider selection
            self.ai = GeminiService()
        else:
            # Fallback or raise error
            raise ValueError(f"Unknown AI provider: {provider}")
        
    def summarize_task(self, task_description: str) -> str:
        """Generate concise task summary."""
        prompt = f"Summarize this task in one concise, actionable sentence: {task_description}"
        # Assuming generate_completion is implemented to accept the 'user' object
        return self.ai.generate_completion(prompt, user=self.user, max_output_tokens=100)
        
    def break_down_task(self, task_description: str) -> List[Dict[str, Any]]:
        """Break epic task into 3-5 subtasks and return as structured JSON."""
        prompt = f"""Break down the following epic task into 3 to 5 highly detailed subtasks.
        Task: {task_description}
        
        Ensure the output is a JSON array that strictly adheres to the provided schema.
        Each subtask must have a title, a detailed description, and an estimated_hours (integer).
        """
        try:
            # Use structured JSON generation with the SubTask Pydantic schema
            json_array = self.ai.generate_structured_json(prompt, user=self.user, schema=List[SubTask])
            return json_array
        except Exception as e:
            # Fallback response structure
            return [{"title": "Error: Breakdown Failed", "description": str(e), "estimated_hours": 1}]
        
    def estimate_effort(self, task_description: str, project_context: Optional[str] = None) -> str:
        """Estimate task effort in hours, providing reasoning."""
        context = f"Project Context: {project_context}\n" if project_context else ""
        prompt = f"""Estimate the effort for the following task in **hours**, and provide a brief justification (1-2 sentences).
        {context}
        Task: {task_description}
        
        Return only the final estimate and justification in the format: 
        "Estimate: X hours. Justification: [Your justification]."
        """
        # Set a low max token count for a concise response
        return self.ai.generate_completion(prompt, user=self.user, max_output_tokens=200, temperature=0.5)
        
    # The remaining methods (suggest_priority, detect_dependencies, suggest_assignee) 
    # would be implemented similarly, using `generate_completion` for free-form text 
    # or `generate_structured_json` for a guaranteed JSON output (e.g., a priority enum).

    def auto_create_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse natural language and create tasks as structured JSON."""
        prompt = f"""Analyze the following natural language text and extract all actionable tasks. 
        Text: "{text}"
        
        For each extracted task, provide a title, a detailed description, and a suggested priority (low, medium, high, or urgent).
        Return the result as a JSON array that strictly adheres to the provided schema.
        """
        try:
            # Use structured JSON generation with the Task Pydantic schema
            json_array = self.ai.generate_structured_json(prompt, user=self.user, schema=List[Task])
            return json_array
        except Exception as e:
            # Fallback response structure
            return [{"title": "Error: Task Extraction Failed", "description": str(e), "priority": "medium"}]