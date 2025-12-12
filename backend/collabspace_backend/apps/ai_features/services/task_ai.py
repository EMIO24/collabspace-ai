import json
import re
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
        print(f"DEBUG: Sending prompt to AI with text: {text[:50]}...")

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
                max_tokens=2000,
                use_pro=use_pro
            )
            
            raw_text = response.get('text', '[]')
            
            # --- DEBUGGING LOGS ---
            print("\n" + "="*50)
            print("DEBUG: RAW AI RESPONSE START")
            print(raw_text)
            print("DEBUG: RAW AI RESPONSE END")
            print("="*50 + "\n")
            # ----------------------

            # 1. Strip Markdown code blocks
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # 2. Regex fallback: Find the first '[' and last ']'
            match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)
            if match:
                cleaned_text = match.group(0)

            # Parse
            tasks = json.loads(cleaned_text)
            
            # Ensure it's a list
            if isinstance(tasks, dict):
                tasks = [tasks]
            
            print(f"DEBUG: Successfully parsed {len(tasks)} tasks.")
            return tasks

        except json.JSONDecodeError as e:
            print(f"ERROR: JSON Parse Error: {e}. Raw text: {raw_text}")
            return [] 
        except Exception as e:
            print(f"ERROR: General Task Extraction Failed: {e}")
            return []

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
                max_tokens=8500,
                use_pro=use_pro
            )
            
            if isinstance(response, dict) and 'error' in response:
                 raise Exception(response['error'])

            raw_text = response.get('text', '[]')
            
            # Debugging
            print(f"DEBUG: Breakdown Raw Response: {raw_text[:100]}...")

            # Cleanup Markdown (Safe multiline checks)
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"): 
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()

            # Regex fallback
            match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)
            if match:
                cleaned_text = match.group(0)

            subtasks = json.loads(cleaned_text)
            return subtasks
        except Exception as e:
            print(f"Warning: Task breakdown failed: {e}")
            raise e # Propagate error

    def estimate_effort(self, user, workspace, task_description: str, project_context: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Estimate task effort in hours, providing justification."""
        context = f"Project Context: {project_context}\n" if project_context else ""
        prompt = f"""{context}Estimate the effort for this task: {task_description}

Provide:
1. Estimated hours (integer)
2. Brief justification

Format: "Estimate: X hours. Justification: [reason]"
"""
        print(f"DEBUG: Requesting estimate for: {task_description[:30]}...")

        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000 # Increased to prevent cut-off
        )
        
        # --- IMPROVED ERROR HANDLING ---
        if isinstance(response, dict) and 'error' in response:
            print(f"ERROR: AI Service failed: {response['error']}")
            return {'estimate': f"Error: {response['error']}"}

        text_response = response.get('text', '')
        if not text_response:
             print(f"DEBUG: Empty response from AI. Full response object: {response}")
             return {'estimate': "AI returned no content."}

        return {'estimate': text_response}

    def suggest_priority(self, user, workspace, task_description: str, due_date: Optional[str] = None, **kwargs) -> Dict[str, str]:
        """Suggest task priority (CRITICAL/HIGH/MEDIUM/LOW)."""
        date_str = f"The due date is {due_date}. " if due_date else ""
        prompt = f"""Based on this task: {task_description}
{date_str}
Suggest the priority level. Choose one: CRITICAL, HIGH, MEDIUM, or LOW.
Return ONLY the priority word."""
        
        print(f"DEBUG: Requesting priority for: {task_description[:30]}...")

        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8100 # Increased to prevent cut-off
        )
        
        # --- IMPROVED ERROR HANDLING ---
        if isinstance(response, dict) and 'error' in response:
            print(f"ERROR: AI Priority failed: {response['error']}")
            return {'priority': f"Error: {response['error']}"}

        raw_text = response.get('text', '').strip().upper()
        
        valid_priorities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'URGENT']
        
        if any(p in raw_text for p in valid_priorities):
            for p in valid_priorities:
                if p in raw_text:
                    return {'priority': p}
        
        print(f"DEBUG: AI returned invalid priority format: '{raw_text}'")
        return {'priority': 'MEDIUM'}

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
            max_tokens=8500
        )
        
        raw_text = response.get('text', '[]')
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        return []

    def suggest_assignee(self, user, workspace, task_description: str, team_members: List[Dict[str, str]], **kwargs) -> Dict[str, str]:
        """Suggest best assignee based on skills (returns name)."""
        
        # 1. DEBUG: Check if we actually received team members
        print(f"DEBUG: Suggesting assignee for task: '{task_description[:30]}...'")
        print(f"DEBUG: Team members received: {len(team_members)}")
        
        if not team_members:
            print("DEBUG: No team members provided to AI.")
            return {'assignee': "No team members available"}

        # Ensure we handle string list or dict list safely
        member_list = "\n- ".join([
            f"{m.get('username', m.get('email', 'Unknown'))}" if isinstance(m, dict) else str(m)
            for m in team_members
        ])
        
        prompt = f"""Task: {task_description}

Team members:
{member_list}

Suggest the most suitable assignee from the list. 
IMPORTANT: Return ONLY the exact username or email. Do not add punctuation or explanation."""
        
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000
        )

        # 2. DEBUG: Check for API Errors
        if isinstance(response, dict) and 'error' in response:
            print(f"ERROR: AI Assignee failed: {response['error']}")
            return {'assignee': f"Error: {response['error']}"}
        
        suggested_name = response.get('text', '').strip()
        print(f"DEBUG: AI suggested: '{suggested_name}'")

        if suggested_name:
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
            max_tokens=8050
        )
        try:
            raw_text = response.get('text', '[]')
            json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
            if json_match:
                 return json.loads(json_match.group(0))
            return []
        except Exception as e:
            print(f"Warning: Failed to parse tag JSON: {e}")
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
            max_tokens=8300
        )
        return response.get('text', 'Failed to draft status update.')