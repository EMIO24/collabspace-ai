from typing import Dict, Any, List, Union
import json
import re
from .gemini_service import GeminiService
from ..utils import truncate_for_context

class AnalyticsAIService:
    """Service class for all AI-powered project and team analytics functionalities."""
    
    FEATURE_TYPE = 'analytics_ai'

    def __init__(self):
        self.ai = GeminiService()

    def _parse_json_response(self, response: Dict[str, Any], default_value: Any) -> Any:
        """
        Helper to safely parse AI response into a Python object (List/Dict).
        Handles Markdown code blocks and common JSON errors.
        """
        # 1. Check for API-level errors (e.g. Rate Limit, Net Error)
        if 'error' in response:
            print(f"ERROR: AI Analytics API Failed: {response['error']}")
            return {'error': response['error']}

        raw_text = response.get('text', '')
        if not raw_text:
            return default_value

        # 2. Strip Markdown code blocks (AI loves adding ```json ... ```)
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()

        # 3. Attempt JSON Parse
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON. Error: {e}")
            print(f"DEBUG: Raw Text causing error: {raw_text[:100]}...")
            # Return a special error dict so the view knows parsing failed, 
            # rather than just returning empty default data (which looks like 'success')
            return {'error': 'Failed to parse AI response', 'raw_response': raw_text}

    def forecast_completion(self, user, workspace, project_data: str, **kwargs) -> Dict[str, Any]:
        """Predict project completion date using Gemini Pro."""
        data_context = truncate_for_context(project_data, max_tokens=16000) 
        prompt = (
            f"Analyze the following project data (velocity, scope, remaining work) and predict "
            f"the final completion date. "
            f"Data: {data_context}\n\n"
            f"Return ONLY a JSON object in this format:\n"
            f'{{"predicted_date": "YYYY-MM-DD", "confidence_score": 85, "risk_factors": ["risk 1", "risk 2"]}}'
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=True
        )
        return self._parse_json_response(response, default_value={})

    def detect_burnout_risk(self, user, workspace, team_data: str, **kwargs) -> Dict[str, Any]:
        """Detect team burnout indicators and suggest mitigation."""
        data_context = truncate_for_context(team_data, max_tokens=8000)
        prompt = (
            f"Analyze team data (overtime, task loads) for burnout risks. "
            f"Data: {data_context}\n\n"
            f"Return ONLY a JSON array of risks in this format:\n"
            f'[{{"username": "john_doe", "risk_score": 85, "reason": "Overloaded", "mitigation": "Reduce load"}}]'
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=False
        )
        return self._parse_json_response(response, default_value=[])

    def analyze_velocity(self, user, workspace, sprint_data: str, use_pro: bool = False, **kwargs) -> Dict[str, Any]:
        """Analyze team velocity trends and suggest improvements."""
        data_context = truncate_for_context(sprint_data, max_tokens=8000)
        prompt = (
            f"Analyze the sprint data for velocity trends. "
            f"Data: {data_context}\n\n"
            f"Return ONLY a JSON object in this format:\n"
            f'{{"trend": "Increasing/Decreasing", "consistency_score": 80, "analysis": "Velocity is stable...", "suggestions": ["fix 1", "fix 2"]}}'
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=False
        )
        return self._parse_json_response(response, default_value={})

    def suggest_resource_allocation(self, user, workspace, workspace_data: str, **kwargs) -> Dict[str, Any]:
        """Suggest optimal resource distribution based on current workload."""
        data_context = truncate_for_context(workspace_data, max_tokens=16000)
        prompt = (
            f"Analyze workspace data (workload, skills) and suggest reallocations. "
            f"Data: {data_context}\n\n"
            f"Return ONLY a JSON object in this format:\n"
            f'{{"current_efficiency": 70, "recommendations": [{{"user": "alice", "action": "move to project B", "reason": "Skill match"}}]}}'
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8500,
            use_pro=True
        )
        return self._parse_json_response(response, default_value={})

    def identify_bottlenecks(self, user, workspace, workflow_data: str, **kwargs) -> Dict[str, Any]:
        """Identify workflow bottlenecks (e.g., long review times)."""
        data_context = truncate_for_context(workflow_data, max_tokens=8000)
        prompt = (
            f"Analyze workflow data (time in status) to find bottlenecks. "
            f"Data: {data_context}\n\n"
            f"Return ONLY a JSON object in this format:\n"
            f'{{"bottlenecks": [{{"stage": "Review", "severity": "High", "avg_time": "4 days", "suggestion": "Add reviewers"}}], "flow_health_score": 65}}'
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=False
        )
        return self._parse_json_response(response, default_value={})