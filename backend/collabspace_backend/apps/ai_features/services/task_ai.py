import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel as PydanticBaseModel, Field

# Local imports
from .gemini_service import GeminiService
from ..models import AIRateLimit 
from django.contrib.auth import get_user_model

User = get_user_model()


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

    def summarize_task(self, user, workspace, task_description, **kwargs):
        """Summarize a task description."""
        prompt = f"Summarize this task in 1-2 sentences: {task_description}"
        response = self.ai.generate_completion(
            user=user, 
            workspace=workspace,
            prompt=prompt, 
            feature_type=self.FEATURE_TYPE, 
            max_tokens=10000
        )
        return response

    def auto_create_from_text(self, user, workspace, text: str, use_pro: bool = False) -> List[Dict[str, Any]]:
        """Parses a block of natural language text and extracts structured tasks."""
        prompt = f"""
Analyze the following natural language text and extract all actionable tasks. 
Text: "{text}"

For each extracted task, provide:
1. A clear, concise title
2. A detailed description
3. A suggested priority (low, medium, high, or urgent)

Return ONLY a valid JSON array of tasks in this exact format:
[
  {{"title": "Task title", "description": "Task description", "priority": "medium"}},
  {{"title": "Another task", "description": "Another description", "priority": "high"}}
]
"""
        try:
            response = self.ai.generate_completion(
                user=user,
                workspace=workspace,
                prompt=prompt,
                feature_type=self.FEATURE_TYPE,
                max_tokens=1000,
                use_pro=use_pro
            )
            
            # Parse the JSON response
            tasks = json.loads(response.get('text', '[]'))
            return tasks
        except Exception as e:
            print(f"Warning: Task extraction failed: {e}")
            return [{"title": "Error: Task Extraction Failed", "description": str(e), "priority": "medium"}]

    def break_down_task(self, user, workspace, task_description: str, num_subtasks: int = 5, use_pro: bool = False) -> List[Dict[str, Any]]:
        """Break epic task into structured subtasks."""
        prompt = f"""
Break down the following epic task into {num_subtasks} detailed subtasks.

Epic Task: {task_description}

For each subtask provide:
1. A clear title
2. Detailed description of steps
3. Estimated hours (integer)

Return ONLY a valid JSON array in this format:
[
  {{"title": "Subtask 1", "description": "Details", "estimated_hours": 4}},
  {{"title": "Subtask 2", "description": "Details", "estimated_hours": 6}}
]
"""
        try:
            response = self.ai.generate_completion(
                user=user,
                workspace=workspace,
                prompt=prompt,
                feature_type=self.FEATURE_TYPE,
                max_tokens=1500,
                use_pro=use_pro
            )
            subtasks = json.loads(response.get('text', '[]'))
            return subtasks
        except Exception as e:
            print(f"Warning: Task breakdown failed: {e}")
            return []

    def estimate_effort(self, user, workspace, task_description: str, project_context: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Estimate task effort in hours, providing justification."""
        context = f"Project Context: {project_context}\n" if project_context else ""
        prompt = f"""{context}Estimate the effort for this task: {task_description}

Provide:
1. Estimated hours (integer)
2. Brief justification

Format: "Estimate: X hours. Justification: [reason]"
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=200
        )
        return {'estimate': response.get('text', 'Failed to generate estimate.')}

    def suggest_priority(self, user, workspace, task_description: str, due_date: Optional[str] = None, **kwargs) -> Dict[str, str]:
        """Suggest task priority (CRITICAL/HIGH/MEDIUM/LOW)."""
        date_str = f"The due date is {due_date}. " if due_date else ""
        prompt = f"""Based on this task: {task_description}
{date_str}
Suggest the priority level. Choose one: CRITICAL, HIGH, MEDIUM, or LOW.
Return ONLY the priority word."""
        
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=10
        )
        priority = response.get('text', 'MEDIUM').strip().upper()
        return {'priority': priority}

    def detect_dependencies(self, user, workspace, task_description: str, existing_tasks: List[str]) -> List[str]:
        """Detect potential task dependencies (returns list of task descriptions)."""
        tasks_list = "\n- ".join(existing_tasks)
        prompt = f"""New task: '{task_description}'

Identify which existing tasks it depends on:
{tasks_list}

Return a JSON array of the dependent task descriptions.
Example: ["Task A", "Task B"]
"""
        
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=500
        )
        try:
            return json.loads(response.get('text', '[]'))
        except json.JSONDecodeError:
            return []

    def suggest_assignee(self, user, workspace, task_description: str, team_members: List[Dict[str, str]], **kwargs) -> Dict[str, str]:
        """Suggest best assignee based on skills (returns name)."""
        member_list = "\n- ".join([f"{m['name']} (Skills: {m.get('skills', 'None listed')})" for m in team_members])
        prompt = f"""Task: {task_description}

Team members:
{member_list}

Suggest the most suitable assignee. Return ONLY the person's name."""
        
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=20
        )
        
        suggested_name = response.get('text', '').strip()
        # Basic validation
        if suggested_name in [m['name'] for m in team_members]:
            return {'assignee': suggested_name}
        return {'assignee': 'Unassigned'}

    def generate_task_tags(self, user, workspace, task_description: str, max_tags: int = 5) -> List[str]:
        """Generate relevant keywords/tags for a task."""
        prompt = f"""Analyze this task and generate up to {max_tags} concise, single-word, lowercase tags.

Task: '{task_description}'

Return a JSON array of strings.
Example: ["backend", "security", "api"]
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=50
        )
        try:
            return json.loads(response.get('text', '[]'))
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse tag JSON: {response.get('text')}")
            return []

    def draft_status_update(self, user, workspace, task_title: str, recent_activities: List[str], target_audience: str = "project manager") -> str:
        """Draft a brief, professional status update based on recent activities."""
        activities_list = "\n- ".join(recent_activities)
        prompt = f"""Draft a professional, concise (2-3 sentences max) status update about task '{task_title}' for a '{target_audience}'.

Recent activities:
- {activities_list}

Focus on progress, blockers, and next steps."""
        
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=300
        )
        return response.get('text', 'Failed to draft status update.')