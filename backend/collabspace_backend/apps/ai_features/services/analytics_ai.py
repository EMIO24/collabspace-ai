from typing import Dict, Any, List
# Local imports
from .gemini_service import GeminiService
from ..utils import truncate_for_context


class AnalyticsAIService:
    """Service class for all AI-powered project and team analytics functionalities."""
    
    FEATURE_TYPE = 'analytics_ai'

    def __init__(self):
        self.ai = GeminiService()

    def _handle_ai_response(self, response: Dict[str, Any], default_key: str, default_message: str) -> Dict[str, str]:
        """
        Processes the response from generate_completion, checking for errors first.
        """
        if 'error' in response:
            return {'error': f"AI Call Failed: {response['error']}"}
        
        # Original logic, now guaranteed to have a 'text' or empty string if no error was returned
        return {default_key: response.get('text', default_message)}

    def forecast_completion(self, user, workspace, project_data: str, **kwargs) -> Dict[str, str]:
        """Predict project completion date using Gemini Pro."""
        data_context = truncate_for_context(project_data, max_tokens=16000) 
        prompt = (
            f"Analyze the following project data (velocity, scope, remaining work) and predict "
            f"the final completion date with a confidence score (High/Medium/Low). "
            f"Your response must be concise and **must not exceed 1000 tokens**.\n" # <-- PROMPT CONTROL ADDED
            f"Data: {data_context}"
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=4000,     # Consistent max token limit (API control)
            use_pro=True         # Retaining Pro for complex forecasting
        )
        return self._handle_ai_response(response, 'forecast', 'Failed to generate forecast.')

    def detect_burnout_risk(self, user, workspace, team_data: str, **kwargs) -> Dict[str, str]:
        """Detect team burnout indicators and suggest mitigation."""
        data_context = truncate_for_context(team_data, max_tokens=8000)
        prompt = (
            f"Analyze team data (overtime, vacation, task reassignment rate) and assess the risk of burnout. "
            f"Provide a risk score (1-5) and 3 mitigation steps. "
            f"Your response must be concise and **must not exceed 1000 tokens**.\n" # <-- PROMPT CONTROL ADDED
            f"Data: {data_context}"
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=4000,     # Consistent max token limit (API control)
            use_pro=False        # Using Flash for speed and cost
        )
        return self._handle_ai_response(response, 'burnout_analysis', 'Failed to detect burnout risk.')

    def analyze_velocity(self, user, workspace, sprint_data: str, use_pro: bool = False, **kwargs) -> Dict[str, str]:
        """Analyze team velocity trends and suggest improvements."""
        data_context = truncate_for_context(sprint_data, max_tokens=8000)
        prompt = (
            f"Analyze the sprint data below to identify velocity trends, consistency, "
            f"and potential areas for process improvement. "
            f"Your response must be concise and **must not exceed 1000 tokens**.\n" # <-- PROMPT CONTROL ADDED
            f"Data: {data_context}"
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=4000,     # Consistent max token limit (API control)
            use_pro=False        # Using Flash for speed and cost
        )
        return self._handle_ai_response(response, 'velocity_analysis', 'Failed to analyze velocity.')

    def suggest_resource_allocation(self, user, workspace, workspace_data: str, **kwargs) -> Dict[str, str]:
        """Suggest optimal resource distribution based on current workload."""
        data_context = truncate_for_context(workspace_data, max_tokens=16000)
        prompt = (
            f"Analyze workspace data (current task load, project priorities, member skills) "
            f"and suggest optimal resource allocation changes. "
            f"Your response must be concise and **must not exceed 1000 tokens**.\n" # <-- PROMPT CONTROL ADDED
            f"Data: {data_context}"
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=4000,     # Consistent max token limit (API control)
            use_pro=True         # Retaining Pro due to complexity
        )
        return self._handle_ai_response(response, 'resource_allocation', 'Failed to suggest resource allocation.')

    def identify_bottlenecks(self, user, workspace, workflow_data: str, **kwargs) -> Dict[str, str]:
        """Identify workflow bottlenecks (e.g., long review times, specific team members)."""
        data_context = truncate_for_context(workflow_data, max_tokens=8000)
        prompt = (
            f"Analyze the workflow data (time in each status, transition rates) to identify "
            f"the top 3 process bottlenecks and suggest concrete fixes. "
            f"Your response must be concise and **must not exceed 1000 tokens**.\n" # <-- PROMPT CONTROL ADDED
            f"Data: {data_context}"
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=4000,     # Consistent max token limit (API control)
            use_pro=False        # Using Flash for speed and cost
        )
        return self._handle_ai_response(response, 'bottlenecks', 'Failed to identify bottlenecks.')