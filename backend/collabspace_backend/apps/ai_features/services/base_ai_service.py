import time
import json
from typing import Optional, Any
from google.generativeai.errors import APIError

# Local imports
from ..models import AIUsage
from ..utils import estimate_tokens, truncate_for_context, get_user_rate_limit


class BaseAIService:
    """Base class for AI service providers, handling usage, limits, and errors."""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 30  # seconds
        # RateLimitHandler logic is merged into AIRateLimit model and checks
        self.rate_limit_model = get_user_rate_limit 

    def count_tokens(self, text: str) -> int:
        """Estimate token count (approx 1 token per 4 chars)."""
        return estimate_tokens(text)

    def handle_rate_limit(self, user) -> bool:
        """Check and enforce Gemini free tier rate limits (60 req/min)."""
        rate_limit = self.rate_limit_model(user)
        return rate_limit.can_make_request()

    def track_usage(self, user, feature_type: str, model_used: str, success: bool, 
                    prompt_tokens: int, completion_tokens: int, processing_time: float,
                    request_data: Dict[str, Any], response_data: Dict[str, Any], 
                    error_message: Optional[str] = None):
        """Track AI usage for quota management."""
        total_tokens = prompt_tokens + completion_tokens
        
        # 1. Log usage
        usage_log = AIUsage.objects.create(
            user=user,
            feature_type=feature_type,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            processing_time=processing_time,
            request_data=truncate_for_context(json.dumps(request_data), max_tokens=1000),
            response_data=truncate_for_context(json.dumps(response_data), max_tokens=1000),
            success=success,
            error_message=error_message,
        )

        # 2. Increment rate limit (Signal handles this based on AIUsage post_save)
        # The signal is set up in signals.py to avoid direct dependency here.
        return usage_log

    def handle_error(self, error: Exception, attempt: int) -> Optional[int]:
        """Handle Gemini API errors gracefully, returning time to wait for retry."""
        if isinstance(error, APIError):
            error_message = str(error).lower()
            
            # Rate Limit or Transient Error: Retry
            if 'rate limit' in error_message or 'unavailable' in error_message or 'timeout' in error_message:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Transient error ({error_message}). Retrying in {wait_time}s. Attempt {attempt}/{self.max_retries}")
                return wait_time
                
            # Content Safety, Invalid Input: Do not retry
            if 'safety' in error_message or 'invalid' in error_message or 'bad request' in error_message:
                print(f"Non-retriable API error: {error_message}")
                return None  # Do not retry

        # All other errors: Retry with backoff
        wait_time = 2 ** attempt
        print(f"Generic error: {error}. Retrying in {wait_time}s. Attempt {attempt}/{self.max_retries}")
        return wait_time