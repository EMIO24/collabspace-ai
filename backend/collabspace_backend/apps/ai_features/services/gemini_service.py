import time
import json
from typing import Dict, Any, List
import google.generativeai as genai
from django.conf import settings
from pydantic import BaseModel as PydanticBaseModel

# Local imports
from .base_ai_service import BaseAIService
from ..utils import (
    calculate_request_hash,
    get_cached_response,
    cache_ai_response,
    get_user_rate_limit,
    format_ai_response,
    truncate_for_context,
    check_content_safety,
)

# Compatibility: APIError replacement for latest genai
APIError = getattr(genai, "Error", Exception)

# --- Safety Configuration ---
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]


class GeminiService(BaseAIService):
    """Service wrapper for Google Generative AI (Gemini / Bison models)."""

    def __init__(self):
        super().__init__()
        gemini_api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set in Django settings.")

        # Configure the module-level client
        genai.configure(api_key=gemini_api_key)

        self.model_flash_name = "models/text-bison-001"  # Free/Flash model
        self.model_pro_name = "models/chat-bison-001"    # Pro model
        self.timeout = 60

    def _get_model(self, use_pro: bool):
        return self.model_pro_name if use_pro else self.model_flash_name

    # ------------------------------
    # Generic Completion
    # ------------------------------
    def generate_completion(self, user, prompt: str, feature_type: str, use_pro: bool = False, max_tokens: int = 1000, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        model_name = self._get_model(use_pro)
        request_hash = calculate_request_hash(prompt, model_name, {"max_output_tokens": max_tokens, "temperature": temperature})
        cached_response = get_cached_response(request_hash)
        if cached_response:
            return format_ai_response({"text": cached_response, "model": model_name, "success": True, "tokens_used": 0})

        if not self.handle_rate_limit(user):
            raise APIError("Rate limit exceeded. Please try again later.")

        try:
            response = genai.generate(
                model=model_name,
                prompt=prompt,
                max_output_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            text = response.candidates[0].content
            cache_ai_response(request_hash, prompt, text, model_name)
            return format_ai_response({"text": text, "model": model_name, "success": True, "tokens_used": response.usage.total_tokens})
        except Exception as e:
            raise APIError(f"Gemini generate_completion failed: {e}") from e

    # ------------------------------
    # Chat
    # ------------------------------
    def generate_chat(self, user, messages: List[Dict[str, str]], feature_type: str, use_pro: bool = False, **kwargs) -> Dict[str, Any]:
        model_name = self._get_model(use_pro)
        if not self.handle_rate_limit(user):
            raise APIError("Rate limit exceeded. Please try again later.")

        formatted_messages = [{"role": msg["role"], "content": msg["text"]} for msg in messages]
        try:
            response = genai.chat.create(
                model=model_name,
                messages=formatted_messages,
                **kwargs
            )
            text = response.last
            return {
                "text": text,
                "model": model_name,
                "total_tokens": response.total_tokens,
                "success": True
            }
        except Exception as e:
            raise APIError(f"Gemini generate_chat failed: {e}") from e

    # ------------------------------
    # Structured JSON
    # ------------------------------
    def generate_structured_json(self, user, prompt: str, feature_type: str, schema: PydanticBaseModel, use_pro: bool = False, **kwargs) -> Any:
        model_name = self._get_model(use_pro)
        if not self.handle_rate_limit(user):
            raise APIError("Rate limit exceeded. Please try again later.")

        try:
            response = genai.generate(
                model=model_name,
                prompt=prompt,
                response_mime_type="application/json",
                **kwargs
            )
            return json.loads(response.candidates[0].content)
        except Exception as e:
            raise APIError(f"Gemini generate_structured_json failed: {e}") from e

    # ------------------------------
    # Moderate / Safety
    # ------------------------------
    def moderate_content(self, text: str) -> bool:
        return check_content_safety(text)

    # ------------------------------
    # With context
    # ------------------------------
    def generate_with_context(self, user, prompt: str, context_data: str, feature_type: str, use_pro: bool = False, **kwargs):
        context_data = truncate_for_context(context_data, max_tokens=250000)
        full_prompt = f"--- CONTEXT ---\n{context_data}\n--- INSTRUCTION ---\n{prompt}"
        return self.generate_completion(user, full_prompt, feature_type, use_pro, **kwargs)
