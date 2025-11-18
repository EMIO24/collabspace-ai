# apps/ai_features/services/analytics_ai.py
from typing import Dict, Any, List
# Local imports
from .gemini_service import GeminiService
from ..utils import truncate_for_context


class AnalyticsAIService:
    """Service class for all AI-powered project and team analytics functionalities."""
    
    FEATURE_TYPE = 'analytics_ai'

    def __init__(self):
        self.ai = GeminiService()

    def forecast_completion(self, user, project_data: str) -> str:
        """Predict project completion date using Gemini Pro."""
        data_context = truncate_for_context(project_data, max_tokens=16000)
        prompt = f"Analyze the following project data (velocity, scope, remaining work) and predict the final completion date with a confidence score (High/Medium/Low). Data: {data_context}"
        response = self.ai.generate_with_context(user, prompt, data_context, self.FEATURE_TYPE, use_pro=True, max_tokens=500)
        return response.get('text', 'Failed to generate forecast.')

    def detect_burnout_risk(self, user, team_data: str) -> str:
        """Detect team burnout indicators and suggest mitigation."""
        data_context = truncate_for_context(team_data, max_tokens=8000)
        prompt = f"Analyze team data (overtime, vacation, task reassignment rate) and assess the risk of burnout. Provide a risk score (1-5) and 3 mitigation steps. Data: {data_context}"
        response = self.ai.generate_with_context(user, prompt, data_context, self.FEATURE_TYPE, use_pro=True, max_tokens=800)
        return response.get('text', 'Failed to detect burnout risk.')

    def analyze_velocity(self, user, sprint_data: str) -> str:
        """Analyze team velocity trends and suggest improvements."""
        data_context = truncate_for_context(sprint_data, max_tokens=8000)
        prompt = f"Analyze the sprint data below to identify velocity trends, consistency, and potential areas for process improvement. Data: {data_context}"
        response = self.ai.generate_with_context(user, prompt, data_context, self.FEATURE_TYPE, max_tokens=1000)
        return response.get('text', 'Failed to analyze velocity.')

    def suggest_resource_allocation(self, user, workspace_data: str) -> str:
        """Suggest optimal resource distribution based on current workload."""
        data_context = truncate_for_context(workspace_data, max_tokens=16000)
        prompt = f"Analyze workspace data (current task load, project priorities, member skills) and suggest optimal resource allocation changes. Data: {data_context}"
        response = self.ai.generate_with_context(user, prompt, data_context, self.FEATURE_TYPE, use_pro=True, max_tokens=1500)
        return response.get('text', 'Failed to suggest resource allocation.')

    def identify_bottlenecks(self, user, workflow_data: str) -> str:
        """Identify workflow bottlenecks (e.g., long review times, specific team members)."""
        data_context = truncate_for_context(workflow_data, max_tokens=8000)
        prompt = f"Analyze the workflow data (time in each status, transition rates) to identify the top 3 process bottlenecks and suggest concrete fixes. Data: {data_context}"
        response = self.ai.generate_with_context(user, prompt, data_context, self.FEATURE_TYPE, use_pro=True, max_tokens=1000)
        return response.get('text', 'Failed to identify bottlenecks.')