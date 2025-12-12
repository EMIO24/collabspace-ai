import json
import re  # Added for robust JSON extraction
from typing import List, Dict, Any, Optional
from pydantic import BaseModel as PydanticBaseModel, Field

# Local imports
from .gemini_service import GeminiService
from ..utils import truncate_for_context


# -------------------------
# Pydantic Schemas
# -------------------------
class ActionItem(PydanticBaseModel):
    title: str = Field(description="The title of the action item/task.")
    assignee: str = Field(description="The person responsible for the action (name or 'Unassigned').")
    due_date: str = Field(description="The suggested due date (e.g., 'next Friday', 'next sprint').")


# -------------------------
# MeetingAIService
# -------------------------
class MeetingAIService:
    """Service class for AI-powered meeting analysis."""

    FEATURE_TYPE = 'meeting_ai'

    def __init__(self):
        self.ai = GeminiService()

    # -------------------------
    # Summarize Meeting
    # -------------------------
    def summarize_meeting(self, user, workspace, transcript: str, **kwargs) -> Dict[str, str]:
        """Summarize meeting transcript with key topics, decisions, and action items."""
        transcript_context = truncate_for_context(transcript, max_tokens=16000)
        prompt = (
            f"Summarize the following meeting transcript. "
            f"Provide sections for 1. Key Topics, 2. Decisions Made, and 3. Next Steps/Action Items.\n"
            f"Transcript:\n{transcript_context}"
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=True
        )
        
        if isinstance(response, dict) and 'error' in response:
             print(f"ERROR: Summarize Meeting failed: {response['error']}")
             return {'summary': f"Error: {response['error']}"}

        return {'summary': response.get('text', 'Failed to generate meeting summary.')}

    # -------------------------
    # Extract Action Items
    # -------------------------
    def extract_action_items(self, user, workspace, transcript: str, use_pro: bool = False, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """Extract action items from meeting transcript."""
        transcript_context = truncate_for_context(transcript, max_tokens=16000)
        prompt = (
            f"From the transcript below, extract all action items. "
            f"For each action item provide:\n"
            f"1. Title\n"
            f"2. Suggested assignee (or 'Unassigned')\n"
            f"3. Suggested due date\n\n"
            f"Return as a JSON array in this format:\n"
            f'[{{"title": "...", "assignee": "...", "due_date": "..."}}]\n\n'
            f"Transcript: {transcript_context}"
        )
        
        print("DEBUG: Extracting action items...")
        
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8500,
            use_pro=use_pro
        )
        
        # 1. Check for API Errors
        if isinstance(response, dict) and 'error' in response:
            print(f"ERROR: Extract Action Items API failed: {response['error']}")
            # We return a special key 'error' inside the list so frontend can see it, 
            # or just return empty list + log. Better to log for now.
            return {'action_items': [], 'error': response['error']}

        raw_text = response.get('text', '[]')
        
        # 2. Robust JSON Parsing (Strip Markdown)
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Regex fallback to find the list
        match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(0)

        try:
            items = json.loads(cleaned_text)
            print(f"DEBUG: Successfully extracted {len(items)} action items.")
            return {'action_items': items}
        except json.JSONDecodeError as e:
            print(f"ERROR: Action Items JSON Parse Error: {e}")
            print(f"DEBUG: Raw Text received: {raw_text}")
            return {'action_items': []}

    # -------------------------
    # Analyze Sentiment
    # -------------------------
    def analyze_sentiment(self, user, workspace, transcript: str, **kwargs) -> Dict[str, str]:
        """Analyze the overall sentiment of the meeting."""
        transcript_context = truncate_for_context(transcript, max_tokens=8000)
        prompt = (
            f"Analyze the overall sentiment of the meeting transcript. "
            f"Return the result in this format: "
            f"'Overall Sentiment: [POSITIVE/NEUTRAL/NEGATIVE]. Rationale: [One concise sentence].' "
            f"\nTranscript: {transcript_context}"
        )
        
        print("DEBUG: Analyzing sentiment...")

        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8050
        )
        
        if isinstance(response, dict) and 'error' in response:
            print(f"ERROR: Sentiment Analysis failed: {response['error']}")
            return {'sentiment': f"Error: {response['error']}"}

        return {'sentiment': response.get('text', 'Failed to analyze sentiment.')}

    # -------------------------
    # Extract Decisions
    # -------------------------
    def extract_decisions(self, user, workspace, transcript: str, **kwargs) -> Dict[str, str]:
        """Extract all key decisions made during the meeting."""
        transcript_context = truncate_for_context(transcript, max_tokens=8000)
        prompt = (
            f"From the transcript below, extract and list all key decisions made. Use bullet points. "
            f"Transcript: {transcript_context}"
        )
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=1000
        )
        
        if isinstance(response, dict) and 'error' in response:
            print(f"ERROR: Extract Decisions failed: {response['error']}")
            return {'decisions': f"Error: {response['error']}"}
            
        return {'decisions': response.get('text', 'Failed to extract decisions.')}

    # -------------------------
    # Draft Follow-Up Email
    # -------------------------
    def draft_follow_up_email(
        self, user, workspace, meeting_summary: str, attendees: List[str], 
        sender: str, include_action_items: bool = True, **kwargs
    ) -> Dict[str, str]:
        """Draft a follow-up email based on meeting summary."""
        attendees_list = ", ".join(attendees)
        action_item_section = ""
        if include_action_items:
            action_item_section = (
                "Please ensure all action items extracted from the meeting are included "
                "in a dedicated 'Action Items' section at the end of the email, listing the owner and due date if known."
            )
        prompt = (
            f"Draft a concise and professional follow-up email for a meeting. "
            f"The email should be sent by {sender} to the attendees: {attendees_list}. "
            f"Use the following summary as the body content, ensuring a clear subject line (e.g., 'Summary: [Meeting Topic]'). "
            f"{action_item_section}.\n\nMeeting Summary:\n{meeting_summary}"
        )
        
        print("DEBUG: Drafting follow-up email...")

        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=False
        )

        if isinstance(response, dict) and 'error' in response:
            print(f"ERROR: Email Draft failed: {response['error']}")
            return {'email': f"Error: {response['error']}"}

        return {'email': response.get('text', 'Failed to draft follow-up email.')}