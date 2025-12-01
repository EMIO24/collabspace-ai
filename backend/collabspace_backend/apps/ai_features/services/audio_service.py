from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model

from .gemini_service import GeminiService
from .base_ai_service import BaseAIService

User = get_user_model()


class AudioService(BaseAIService):
    """
    Service to handle Speech-to-Text (STT) transcription using Gemini's multimodal capability.
    """
    FEATURE_TYPE = 'task_ai_audio'  # Separate feature type for stricter rate limits
    
    def __init__(self):
        super().__init__()
        self.ai = GeminiService()

    def transcribe(self, user: User, workspace, file_path: str, use_pro: bool = False, mime_type: str = 'audio/mp3') -> Optional[str]:
        """
        Processes an audio file, sends it to Gemini for transcription, and returns the text.
        
        Args:
            user: The user object for rate limiting and logging
            workspace: The workspace context
            file_path: The local path to the audio file
            use_pro: Whether to use Pro model
            mime_type: The MIME type of the audio file
            
        Returns:
            The transcribed text string or None on failure
        """
        
        # 1. Rate Limit Check (High-Cost operation - cost=5)
        try:
            self.handle_rate_limit(user, feature_type=self.FEATURE_TYPE, cost=5)
        except Exception as e:
            print(f"Rate Limit Error for transcription: {e}")
            raise e
        
        # 2. Call Gemini for transcription
        try:
            # Note: You'll need to implement generate_audio_transcription in GeminiService
            # For now, this is a placeholder that reads the file and processes it
            
            # Placeholder implementation:
            # In a real implementation, you would upload the audio file to Gemini
            # and use its multimodal capabilities
            
            prompt = f"Transcribe the following audio file accurately: {file_path}"
            
            response = self.ai.generate_completion(
                user=user,
                workspace=workspace,
                prompt=prompt,
                feature_type=self.FEATURE_TYPE,
                use_pro=use_pro,
                max_tokens=4096
            )
            
            return response.get('text', None)
        
        except Exception as e:
            print(f"Gemini transcription failed: {e}")
            
            # Log the failed attempt
            try:
                self.log_usage(
                    user=user,
                    workspace=workspace,
                    feature_type=self.FEATURE_TYPE,
                    prompt_tokens=0,
                    completion_tokens=0,
                    success=False,
                    error_message=str(e)
                )
            except:
                pass
            
            return None