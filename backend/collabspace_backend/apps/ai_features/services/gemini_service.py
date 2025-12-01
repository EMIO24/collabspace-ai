import os
import logging
from typing import Dict, Any, Union, Optional, List
from django.conf import settings
import google.generativeai as genai
import google.generativeai.types as types

# Local imports (assuming correct path)
from .base_ai_service import BaseAIService
from ..models import AIUsage, AICache 

# Set up logger for the module
logger = logging.getLogger(__name__)

class GeminiService(BaseAIService):
    """Service for interacting with Google's Gemini AI models."""
    
    FEATURE_TYPE: str = 'gemini'
    
    def __init__(self):
        """Initialize Gemini service with API configuration."""
        super().__init__()
        
        # Configure the Gemini API
        api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY'))
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in settings or environment variables")
        
        genai.configure(api_key=api_key)
        
        self.flash_model_name: str = 'gemini-2.5-flash'
        self.pro_model_name: str = 'gemini-2.5-pro'

    def _get_model(self, use_pro: bool = False) -> genai.GenerativeModel:
        """Get the appropriate Gemini model."""
        model_name = self.pro_model_name if use_pro else self.flash_model_name
        return genai.GenerativeModel(model_name)

    # FIX: Using List[Any] to avoid module import errors with specific SDK versions
    def _format_safety_details(self, ratings: List[Any]) -> str:
        """Helper to format safety ratings into a readable string."""
        return ", ".join([
            f"{r.category.name}:{r.probability.name}" 
            for r in ratings
        ])

    def _check_for_blocks(self, response: types.GenerateContentResponse, prompt: str, user, workspace, feature_type: str, model_name: str) -> Optional[Dict[str, str]]:
        """
        Checks the API response for content blocks (safety, resource exhaustion, etc.).
        
        Returns a dictionary {'error': message} if blocked, or None otherwise.
        """
        
        # 1. Check for prompt-level blocks (no candidates returned)
        if not response.candidates:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
                safety_ratings = response.prompt_feedback.safety_ratings
                safety_details = self._format_safety_details(safety_ratings) if safety_ratings else "N/A"
                error_message = f"Prompt blocked: {block_reason}. Safety Details: {safety_details}"
            else:
                error_message = "API response contained no candidates and no clear block reason."
            
            logger.warning(f"Gemini generation blocked/failed: {error_message} (Model: {model_name})")
            
            # FIX: Added required token arguments for log_usage (Estimate prompt tokens)
            self.log_usage(
                user=user, workspace=workspace, feature_type=feature_type, success=False,
                error_message=error_message, model_used=model_name, provider='gemini',
                prompt_tokens=self.estimate_tokens(prompt),
                completion_tokens=0,
            )
            return {'error': error_message}
        
        # 2. Check for candidate-specific blocks (finish_reason != STOP)
        candidate = response.candidates[0]
        if candidate.finish_reason.name != 'STOP':
            block_reason = candidate.finish_reason.name
            
            if block_reason == 'SAFETY' and candidate.safety_ratings:
                safety_details = self._format_safety_details(candidate.safety_ratings)
                error_message = f"Response blocked by Safety Filter ({block_reason}). Details: {safety_details}"
            else:
                error_message = f"Response stopped prematurely. Finish Reason: {block_reason}."
            
            logger.warning(f"Gemini generation blocked/failed: {error_message} (Model: {model_name})")

            # Try to get prompt tokens from metadata for accurate logging on failure, otherwise estimate
            prompt_tokens_fail = getattr(response.usage_metadata, 'prompt_token_count', 0)
            if prompt_tokens_fail == 0:
                 prompt_tokens_fail = self.estimate_tokens(prompt)

            # FIX: Added required token arguments for log_usage
            self.log_usage(
                user=user, workspace=workspace, feature_type=feature_type, success=False,
                error_message=error_message, model_used=model_name, provider='gemini',
                prompt_tokens=prompt_tokens_fail,
                completion_tokens=0,
            )
            return {'error': error_message}
        
        return None # No block found
    
    def generate_completion(self, user, workspace, prompt: str, feature_type: str, max_tokens: int = 500, use_pro: bool = False) -> Dict[str, Union[str, int]]:
        """
        Generate a completion using Gemini.
        
        Returns:
            Dict[str, Any]: A dictionary containing 'text' or 'error' key.
        """
        model_name = self.pro_model_name if use_pro else self.flash_model_name
        
        try:
            self.handle_rate_limit(user, feature_type=feature_type, cost=1)
            model = self._get_model(use_pro=use_pro)
            
            response = model.generate_content(
                prompt,
                generation_config=types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )
            
            # Check for content blocks using helper
            block_check = self._check_for_blocks(response, prompt, user, workspace, feature_type, model_name)
            if block_check:
                return block_check
            
            # --- Successful Response Path ---
            
            response_text = response.text
            
            # Get token usage
            try:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count
                total_tokens = response.usage_metadata.total_token_count
            except AttributeError:
                # Fallback estimation if metadata is unavailable
                prompt_tokens = self.estimate_tokens(prompt)
                completion_tokens = self.estimate_tokens(response_text)
                total_tokens = prompt_tokens + completion_tokens
            
            # Log usage
            self.log_usage(
                user=user, workspace=workspace, feature_type=feature_type,
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                model_used=model_name, provider='gemini', success=True,
                request_data={'prompt': prompt[:500]}, response_data={'text': response_text[:500]},
            )
            
            return {
                'text': response_text,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'model': model_name
            }
            
        except Exception as e:
            # Handle API errors, rate limits, network issues, etc.
            error_msg = f"Gemini generate_completion failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            # Log failure
            try:
                # FIX: Provided required token arguments with zero values for generic exceptions
                self.log_usage(
                    user=user, workspace=workspace, feature_type=feature_type, success=False,
                    error_message=str(e), model_used=model_name, provider='gemini',
                    prompt_tokens=0,
                    completion_tokens=0,
                )
            except:
                pass 
                
            return {'error': str(e)}

    def generate_chat(self, user, workspace, messages: List[Dict[str, str]], feature_type: str, use_pro: bool = False) -> Dict[str, Union[str, int]]:
        """
        Generate a chat response using Gemini.
        """
        model_name = self.pro_model_name if use_pro else self.flash_model_name

        try:
            self.handle_rate_limit(user, feature_type=feature_type, cost=1)
            model = self._get_model(use_pro=use_pro)
            chat = model.start_chat(history=[])
            
            # Convert messages to Gemini format and build history
            for msg in messages[:-1]:
                role = 'model' if msg['role'] == 'assistant' else 'user'
                chat.history.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(msg['text'])]
                ))
            
            # Send the last message
            last_message = messages[-1]['text']
            response = chat.send_message(last_message)
            
            # Check for content blocks using helper
            block_check = self._check_for_blocks(response, last_message, user, workspace, feature_type, model_name)
            if block_check:
                return block_check

            # Extract response
            response_text = response.text
            
            # Get token usage
            try:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count
                total_tokens = response.usage_metadata.total_token_count
            except AttributeError:
                # Fallback estimation
                all_text = ' '.join([m['text'] for m in messages]) + response_text
                prompt_tokens = self.estimate_tokens(all_text)
                completion_tokens = self.estimate_tokens(response_text)
                total_tokens = prompt_tokens + completion_tokens
            
            # Log usage
            self.log_usage(
                user=user, workspace=workspace, feature_type=feature_type,
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                model_used=model_name, provider='gemini', success=True,
            )
            
            return {
                'text': response_text,
                'total_tokens': total_tokens,
                'model': model_name
            }
            
        except Exception as e:
            error_msg = f"Gemini chat failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            try:
                # FIX: Provided required token arguments with zero values for generic exceptions
                self.log_usage(
                    user=user, workspace=workspace, feature_type=feature_type,
                    prompt_tokens=0, completion_tokens=0,
                    model_used=model_name, provider='gemini',
                    success=False, error_message=str(e),
                )
            except:
                pass
            
            return {'error': str(e)}
    
    def check_cache(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """Check if a cached response exists for this prompt."""
        try:
            cache_entry = AICache.objects.get(prompt_hash=prompt_hash)
            return cache_entry.response_data
        except AICache.DoesNotExist:
            return None
    
    def save_to_cache(self, prompt_hash: str, response_data: Dict[str, Any]):
        """Save a response to the cache."""
        AICache.objects.create(
            prompt_hash=prompt_hash,
            response_data=response_data
        )