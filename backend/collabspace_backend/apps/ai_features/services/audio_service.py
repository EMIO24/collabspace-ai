from typing import Optional, Dict, Any
from .gemini_service import GeminiService
from ..models import AIRateLimit # For rate limit tracking
from ..models import User # Assuming User is imported/defined here

class AudioService:
    """
    Service to handle Speech-to-Text (STT) transcription using Gemini's multimodal capability.
    """
    FEATURE_TYPE = 'task_ai_audio' # Separate feature type for stricter rate limits
    
    def __init__(self):
        # The GeminiService is used here to handle the actual file API and transcription call.
        # This keeps the audio service clean and focused on orchestration.
        self.ai = GeminiService()

    def transcribe(self, user: User, file_path: str, use_pro: bool = False, mime_type: str = 'audio/mp3') -> Optional[str]:
        """
        Processes an audio file, sends it to Gemini for transcription, and returns the text.
        
        :param user: The user object for rate limiting and logging.
        :param file_path: The local path to the audio file.
        :return: The transcribed text string or None on failure.
        """
        
        # 1. Rate Limit Check (High-Cost operation - cost=5)
        try:
            # We track the initial transcription cost here
            AIRateLimit.track_usage(user, self.FEATURE_TYPE, cost=5) 
        except Exception as e:
            print(f"Rate Limit Error for transcription: {e}")
            raise e # Propagate the error up to the TaskAIService
        
        # 2. Call Gemini for transcription
        try:
            response = self.ai.generate_audio_transcription(
                user=user, 
                audio_file_path=file_path, 
                feature_type=self.FEATURE_TYPE, 
                use_pro=use_pro,
                mime_type=mime_type
            )
            return response.get('text', None)
        
        except Exception as e:
            # Note: The file cleanup is handled inside GeminiService.generate_audio_transcription
            print(f"Gemini transcription failed: {e}")
            return None