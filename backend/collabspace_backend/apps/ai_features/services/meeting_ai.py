import json
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
    # Prepare Gemini Content
    # -------------------------
    def _prepare_gemini_content(self, file_path: str, prompt: str) -> List[dict]:
        """
        Prepare multimodal content for Gemini (audio/video/text).
        This replaces the old types.Content usage.
        """
        # Placeholder: replace with actual file upload logic
        file_reference = "<uploaded_file_reference>"

        # Each content is a dict with role and list of parts (type/text)
        return [
            {
                "role": "system",
                "content": [{"type": "text", "text": file_reference}]
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]

    # -------------------------
    # Transcribe Audio
    # -------------------------
    def transcribe_audio(self, user, audio_file_path: str, use_pro: bool = True) -> str:
        """Transcribe audio using Gemini multimodal model."""
        prompt = "Transcribe the audio accurately. Focus on speaker clarity and context."
        contents = self._prepare_gemini_content(audio_file_path, prompt)

        response = self.ai.generate_from_contents(
            user,
            contents,  # List of dicts now
            feature_type=self.FEATURE_TYPE,
            use_pro=use_pro,
            max_tokens=4096,
            temperature=0.1
        )
        return response.get('text', f"AI Transcription Error: Could not process {audio_file_path}")

    # -------------------------
    # Summarize Meeting
    # -------------------------
    def summarize_meeting(self, user, transcript: str) -> str:
        transcript_context = truncate_for_context(transcript, max_tokens=16000)
        prompt = (
            f"Summarize the following meeting transcript. "
            f"Provide sections for 1. Key Topics, 2. Decisions Made, and 3. Next Steps/Action Items.\n"
            f"Transcript:\n{transcript_context}"
        )
        response = self.ai.generate_with_context(
            user, prompt, transcript_context, self.FEATURE_TYPE, use_pro=True, max_tokens=4000
        )
        return response.get('text', 'Failed to generate meeting summary.')

    # -------------------------
    # Extract Action Items
    # -------------------------
    def extract_action_items(self, user, transcript: str, use_pro: bool = False) -> List[Dict[str, Any]]:
        transcript_context = truncate_for_context(transcript, max_tokens=16000)
        prompt = (
            f"From the transcript below, extract all action items. "
            f"Provide the title, suggested assignee, and suggested due date for each. "
            f"Transcript: {transcript_context}"
        )
        return self.ai.generate_structured_json(
            user, prompt, self.FEATURE_TYPE, schema=List[ActionItem], use_pro=use_pro
        )

    # -------------------------
    # Analyze Sentiment
    # -------------------------
    def analyze_sentiment(self, user, transcript: str) -> str:
        transcript_context = truncate_for_context(transcript, max_tokens=8000)
        prompt = (
            f"Analyze the overall sentiment of the meeting transcript. "
            f"Return the result in a single sentence: "
            f"'Overall Sentiment: [POSITIVE/NEUTRAL/NEGATIVE]. Rationale: [One concise sentence].' "
            f"\nTranscript: {transcript_context}"
        )
        response = self.ai.generate_with_context(user, prompt, transcript_context, self.FEATURE_TYPE, max_tokens=150)
        return response.get('text', 'Failed to analyze sentiment.')

    # -------------------------
    # Extract Decisions
    # -------------------------
    def extract_decisions(self, user, transcript: str) -> str:
        transcript_context = truncate_for_context(transcript, max_tokens=8000)
        prompt = (
            f"From the transcript below, extract and list all key decisions made. Use bullet points. "
            f"Transcript: {transcript_context}"
        )
        response = self.ai.generate_with_context(user, prompt, transcript_context, self.FEATURE_TYPE)
        return response.get('text', 'Failed to extract decisions.')

    # -------------------------
    # Draft Follow-Up Email
    # -------------------------
    def draft_follow_up_email(
        self, user, meeting_summary: str, attendees: List[str], sender: str, include_action_items: bool = True
    ) -> str:
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
        response = self.ai.generate_with_context(
            user, prompt, meeting_summary, self.FEATURE_TYPE, use_pro=False, max_tokens=1000, temperature=0.7
        )
        return response.get('text', 'Failed to draft follow-up email.')
