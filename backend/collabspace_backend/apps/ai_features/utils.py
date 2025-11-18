import hashlib
import json
import time
import os
from datetime import timedelta
from django.utils import timezone
from .models import AICache, AIRateLimit

# --- Caching and Hashing ---

def calculate_request_hash(prompt: str, model: str, params: Dict[str, Any]) -> str:
    """Calculate hash for caching AI responses based on input parameters."""
    # Ensure consistent order for dict keys in params
    cache_key = f"{prompt}_{model}_{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(cache_key.encode('utf-8')).hexdigest()

def cache_ai_response(request_hash: str, prompt: str, response_text: str, model_used: str):
    """Cache AI responses to reduce API calls."""
    try:
        AICache.objects.create(
            request_hash=request_hash,
            prompt=prompt[:5000],  # Truncate prompt for storage
            response=response_text[:5000],  # Truncate response
            model_used=model_used
        )
    except Exception as e:
        # Fail silently on cache error
        print(f"Cache failed: {e}")

def get_cached_response(request_hash: str) -> Optional[str]:
    """Get cached AI response if exists and not expired."""
    try:
        cached = AICache.objects.get(request_hash=request_hash)
        if not cached.is_expired():
            cached.access_count += 1
            cached.last_accessed = timezone.now()
            cached.save()
            return cached.response
    except AICache.DoesNotExist:
        pass
    except Exception as e:
        # Fail silently on cache error
        print(f"Cache retrieval failed: {e}")
    return None

# --- Token and Safety ---

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
    # This is a safe approximation for estimation, but the model should return the actual count
    return len(text) // 4

def truncate_for_context(text: str, max_tokens: int = 32000) -> str:
    """Truncate text to fit within Gemini context window (4 chars per token)."""
    # Leaving some buffer
    max_chars = int(max_tokens * 3.5) 
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [TRUNCATED]"

def check_content_safety(text: str) -> bool:
    """Placeholder for content safety check (e.g., using Gemini moderation)."""
    # In production, this would use a dedicated API call or a pre-configured check
    # For now, we assume content is safe.
    return True 

def format_ai_response(raw_response: Dict[str, Any]) -> Dict[str, Any]:
    """Format AI response for frontend/logging."""
    return {
        'text': raw_response.get('text', ''),
        'model': raw_response.get('model', 'gemini-1.5-flash'),
        'prompt_tokens': raw_response.get('prompt_tokens', 0),
        'completion_tokens': raw_response.get('completion_tokens', 0),
        'total_tokens': raw_response.get('total_tokens', 0),
        'processing_time': raw_response.get('processing_time'),
        'success': raw_response.get('success', False),
    }

def get_user_rate_limit(user) -> AIRateLimit:
    """Get or create the user's rate limit entry."""
    rate_limit, _ = AIRateLimit.objects.get_or_create(user=user)
    # Ensure limits are up-to-date before checking
    rate_limit.reset_if_needed()
    return rate_limit