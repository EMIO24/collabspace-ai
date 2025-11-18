import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel as PydanticBaseModel, Field

# Local imports
from .gemini_service import GeminiService
from ..utils import truncate_for_context
# Placeholder import for the Gemini API wrapper and types (needed for transcribe_audio)
from google.genai import types 


# Define Pydantic Schemas
class ActionItem(PydanticBaseModel):
    title: str = Field(description="The title of the action item/task.")
    assignee: str = Field(description="The person responsible for the action (name or 'Unassigned').")
    due_date: str = Field(description="The suggested due date (e.g., 'next Friday', 'next sprint').")


class MeetingAIService:
    """Service class for all AI-powered meeting analysis functionalities."""
    
    FEATURE_TYPE = 'meeting_ai'

    def __init__(self):
        self.ai = GeminiService()

    # --- Utility for Transcribe (Assumes a file management system) ---

    def _prepare_gemini_content(self, file_path: str, prompt: str) -> List[types.Part]:
        """
        Placeholder for uploading file and preparing multimodal content for Gemini.
        NOTE: This requires access to the low-level Gemini client and file upload/delete logic.
        """
        # In a real environment, this would upload the file and return a parts list
        # For this context, we will mock the content structure.
        class MockPart:
            def __init__(self, text):
                self.text = text
        
        return [
            MockPart(text="<audio_file_reference>"),
            types.Content(role="user", parts=[types.Part.from_text(prompt)])
        ]
    
    # --- ADDED: Transcribe Audio Function ---

    def transcribe_audio(self, user, audio_file_path: str, use_pro: bool = True) -> str:
        """Transcribe audio using a multimodal model (Gemini)."""
        # NOTE: This implementation relies on a fully implemented GeminiService 
        # that can handle the actual file upload and multimodal call.
        prompt = "Transcribe the audio accurately. Focus on speaker clarity and context."
        
        # Use a dedicated method in GeminiService for multimodal/file-based tasks
        # This assumes the GeminiService handles the file lifecycle (upload/delete).
        response = self.ai.generate_from_file(
            user, 
            prompt, 
            audio_file_path, 
            self.FEATURE_TYPE, 
            use_pro=use_pro,
            max_tokens=4096,
            temperature=0.1
        )
        return response.get('text', f"AI Transcription Error: Could not process {audio_file_path}")

    # --- EXISTING METHODS ---

    def summarize_meeting(self, user, transcript: str) -> str:
        """Generate a structured meeting summary (key points, context, next steps)."""
        transcript_context = truncate_for_context(transcript, max_tokens=16000)
        prompt = f"Summarize the following meeting transcript. Provide sections for 1. Key Topics, 2. Decisions Made, and 3. Next Steps/Action Items.\nTranscript:\n{transcript_context}"
        response = self.ai.generate_with_context(user, prompt, transcript_context, self.FEATURE_TYPE, use_pro=True, max_tokens=4000)
        return response.get('text', 'Failed to generate meeting summary.')

    def extract_action_items(self, user, transcript: str, use_pro: bool = False) -> List[Dict[str, Any]]:
        """Extract action items as structured tasks (title, assignee, due_date)."""
        transcript_context = truncate_for_context(transcript, max_tokens=16000)
        prompt = f"From the transcript below, extract all action items. Provide the title, suggested assignee, and suggested due date for each. Transcript: {transcript_context}"
        return self.ai.generate_structured_json(user, prompt, self.FEATURE_TYPE, schema=List[ActionItem], use_pro=use_pro)

    def analyze_sentiment(self, user, transcript: str) -> str:
        """Analyze meeting sentiment (overall and key segments) and provide rationale."""
        transcript_context = truncate_for_context(transcript, max_tokens=8000)
        # Modified prompt to match the requested output format from the original snippet
        prompt = (
            f"Analyze the overall sentiment of the meeting transcript. Return the result in a single sentence: "
            f"'Overall Sentiment: [POSITIVE/NEUTRAL/NEGATIVE]. Rationale: [One concise sentence].'"
            f"\nTranscript: {transcript_context}"
        )
        response = self.ai.generate_with_context(user, prompt, transcript_context, self.FEATURE_TYPE, max_tokens=150)
        return response.get('text', 'Failed to analyze sentiment.')

    def extract_decisions(self, user, transcript: str) -> str:
        """Extract key decisions made during the meeting."""
        transcript_context = truncate_for_context(transcript, max_tokens=8000)
        prompt = f"From the transcript below, extract and list all key decisions made. Use bullet points. Transcript: {transcript_context}"
        response = self.ai.generate_with_context(user, prompt, transcript_context, self.FEATURE_TYPE)
        return response.get('text', 'Failed to extract decisions.')

    # --- ADDED: Draft Follow-Up Email Function ---

    def draft_follow_up_email(self, user, meeting_summary: str, attendees: List[str], sender: str, include_action_items: bool = True) -> str:
        """
        Drafts a professional follow-up email based on the meeting summary.
        """
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
            f"{action_item_section}."
            f"\n\nMeeting Summary:\n{meeting_summary}"
        )
        
        response = self.ai.generate_with_context(user, prompt, meeting_summary, self.FEATURE_TYPE, use_pro=False, max_tokens=1000, temperature=0.7)
        return response.get('text', 'Failed to draft follow-up email.')