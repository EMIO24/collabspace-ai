import time
import json
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from google.generativeai.errors import APIError
from google.generativeai import types
from django.conf import settings
from pydantic import BaseModel as PydanticBaseModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Local imports
from .base_ai_service import BaseAIService
from ..utils import calculate_request_hash, get_cached_response, cache_ai_response, get_user_rate_limit, format_ai_response

# Placeholder for Pydantic (Assuming Pydantic is installed)
# We must re-declare the schemas if we don't import them from task_ai.py
class BaseModel: pass # Placeholder
class Field: pass # Placeholder

# --- Safety Configuration ---
# Set safety settings to block harmful content
SAFETY_SETTINGS = [
    types.SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
    types.SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
    types.SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
    types.SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
]


class GeminiService(BaseAIService):
    """
    Handles all interactions with the Google Gemini API, including configuration,
    rate limiting, retries, and usage tracking.
    """
    def __init__(self):
        super().__init__()
        
        # Configuration
        gemini_api_key = settings.GEMINI_API_KEY
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set in Django settings.")

        genai.configure(api_key=gemini_api_key)
        
        # Models
        self.model_flash_name = 'gemini-1.5-flash'
        self.model_pro_name = 'gemini-1.5-pro'
        
        # Use Client for more control and efficiency
        self.client = genai.Client(api_key=gemini_api_key)
        self.model_flash = self.client.models.get(self.model_flash_name)
        self.model_pro = self.client.models.get(self.model_pro_name)

    def _get_model(self, use_pro: bool):
        """Returns the GenerativeModel instance and its name."""
        if use_pro:
            return self.client.models.get(self.model_pro_name), self.model_pro_name
        return self.client.models.get(self.model_flash_name), self.model_flash_name

    def _call_gemini_api(self, model_name: str, contents: Any, config: types.GenerateContentConfig) -> types.GenerateContentResponse:
        """Internal function to handle the actual API call."""
        start_time = time.time()
        
        # Use client.models.generate_content for specific model calls
        response = self.client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
            # Pass the timeout to the API call itself
            request_options={'timeout': self.timeout}
        )
        end_time = time.time()
        
        # Check for blocked content
        if not response.candidates:
            raise APIError(f"Content blocked by safety settings: {response.prompt_feedback.block_reason.name}")

        return response, end_time - start_time

    def generate_completion(self, user, prompt: str, feature_type: str, use_pro: bool = False, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """
        Generate text completion using Gemini with rate limiting, retries, and usage tracking.
        Returns a formatted dictionary containing the response text and metadata.
        """
        
        model, model_name = self._get_model(use_pro)
        
        # 1. Check Cache
        config_params = {'max_output_tokens': max_tokens, 'temperature': temperature}
        request_hash = calculate_request_hash(prompt, model_name, config_params)
        cached_response = get_cached_response(request_hash)
        if cached_response:
            return format_ai_response({
                'text': cached_response, 
                'model': model_name, 
                'success': True,
                'tokens_used': 0 # Indicate cache hit
            })
            
        # 2. API Call with Retries and Tracking
        attempt = 0
        while attempt < self.max_retries:
            
            # Rate Limit Check
            if not self.handle_rate_limit(user):
                raise APIError("Rate limit exceeded. Please try again in a minute.")
            
            try:
                config = types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    safety_settings=SAFETY_SETTINGS,
                    **kwargs
                )
                
                response, processing_time = self._call_gemini_api(model_name, prompt, config)
                
                # Extract token usage
                usage_metadata = response.usage_metadata
                prompt_tokens = usage_metadata.prompt_token_count
                completion_tokens = usage_metadata.candidates_token_count
                
                final_response = {
                    'text': response.text,
                    'model': model_name,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': prompt_tokens + completion_tokens,
                    'processing_time': processing_time,
                    'success': True
                }

                # 3. Cache and Track
                cache_ai_response(request_hash, prompt, final_response['text'], model_name)
                self.track_usage(user, feature_type, model_name, True, prompt_tokens, completion_tokens, processing_time, {'prompt': prompt, 'config': config_params}, final_response)
                
                return final_response
            
            except APIError as e:
                attempt += 1
                wait_time = self.handle_error(e, attempt)
                
                if wait_time is not None and attempt < self.max_retries:
                    time.sleep(wait_time)
                else:
                    # Final failure after retries
                    self.track_usage(user, feature_type, model_name, False, self.count_tokens(prompt), 0, time.time() - start_time, {'prompt': prompt, 'config': config_params}, {}, str(e))
                    raise APIError(f"Gemini API failed after {attempt} attempts: {e}") from e

        # Should be unreachable
        raise APIError("Gemini API call failed unexpectedly.")


    def generate_structured_json(self, user, prompt: str, feature_type: str, schema: PydanticBaseModel, use_pro: bool = False, temperature: float = 0.7, **kwargs) -> List[Dict[str, Any]]:
        """
        Generates content structured according to a Pydantic schema (JSON output).
        Returns a list of dictionaries parsed from the JSON response.
        """
        
        model, model_name = self._get_model(use_pro)
        
        # 1. API Call with Retries
        attempt = 0
        while attempt < self.max_retries:
            
            if not self.handle_rate_limit(user):
                raise APIError("Rate limit exceeded. Please try again in a minute.")
            
            try:
                # Configure structured output
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=temperature,
                    safety_settings=SAFETY_SETTINGS,
                    **kwargs
                )
                
                response, processing_time = self._call_gemini_api(model_name, prompt, config)
                
                # Extract token usage
                usage_metadata = response.usage_metadata
                prompt_tokens = usage_metadata.prompt_token_count
                completion_tokens = usage_metadata.candidates_token_count
                
                # The response.text is guaranteed to be a valid JSON string matching the schema
                json_data = json.loads(response.text)

                # 2. Track Usage
                self.track_usage(user, feature_type, model_name, True, prompt_tokens, completion_tokens, processing_time, {'prompt': prompt, 'schema': str(schema)}, {'json': json_data})

                return json_data
            
            except APIError as e:
                attempt += 1
                wait_time = self.handle_error(e, attempt)
                if wait_time is not None and attempt < self.max_retries:
                    time.sleep(wait_time)
                else:
                    # Final failure
                    self.track_usage(user, feature_type, model_name, False, self.count_tokens(prompt), 0, time.time() - start_time, {'prompt': prompt}, {}, str(e))
                    raise APIError(f"Gemini structured generation failed: {e}") from e

        raise APIError("Gemini structured generation failed unexpectedly.")

    def generate_chat(self, user, messages: List[Dict[str, str]], feature_type: str, use_pro: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Multi-turn conversation using Gemini chat API.
        The `messages` list should be a sequence of roles (user/model) and content.
        """
        model, model_name = self._get_model(use_pro)
        
        # Convert simple list of dicts to Content objects
        contents = [
            types.Content(role=msg['role'], parts=[types.Part.from_text(msg['text'])])
            for msg in messages
        ]
        
        try:
            # 1. Rate Limit Check
            if not self.handle_rate_limit(user):
                raise APIError("Rate limit exceeded. Please try again in a minute.")
                
            config = types.GenerateContentConfig(safety_settings=SAFETY_SETTINGS, **kwargs)
            
            # Start time measurement outside of internal call
            start_time = time.time()
            response, processing_time = self._call_gemini_api(model_name, contents, config)
            
            # Extract token usage
            usage_metadata = response.usage_metadata
            prompt_tokens = usage_metadata.prompt_token_count
            completion_tokens = usage_metadata.candidates_token_count
            
            final_response = {
                'text': response.text,
                'model': model_name,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
                'processing_time': processing_time,
                'success': True
            }

            # 2. Track Usage
            self.track_usage(user, feature_type, model_name, True, prompt_tokens, completion_tokens, processing_time, {'messages': messages}, final_response)
            
            return final_response
            
        except APIError as e:
            # No retry logic implemented here for simplicity, but could be added
            self.track_usage(user, feature_type, model_name, False, self.count_tokens(json.dumps(messages)), 0, time.time() - start_time, {'messages': messages}, {}, str(e))
            raise APIError(f"Gemini Chat API failed: {e}") from e

    def generate_with_context(self, user, prompt: str, context_data: str, feature_type: str, use_pro: bool = False, **kwargs) -> Dict[str, Any]:
        """Generate with additional context (e.g., embeddings results, documents)."""
        
        # Truncate context to avoid exceeding context window limits
        context_data = truncate_for_context(context_data, max_tokens=250000)
        
        full_prompt = (
            f"--- CONTEXT ---\n{context_data}\n--- INSTRUCTION ---\n{prompt}"
        )
        
        # Use a higher max_tokens for context-heavy tasks
        max_tokens = kwargs.pop('max_tokens', 8000)
        
        return self.generate_completion(user, full_prompt, feature_type, use_pro, max_tokens, **kwargs)

    def moderate_content(self, text: str) -> bool:
        """
        Check content safety using Gemini's built-in safety classifier.
        Returns True if content is safe (i.e., not blocked).
        """
        # This is already handled by SAFETY_SETTINGS in generate_completion, 
        # but a dedicated check might be needed for user input prior to API calls.
        return check_content_safety(text)