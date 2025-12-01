import hashlib
import json
import time
import os
import logging # <-- ADDED for proper error logging
from datetime import timedelta
from django.utils import timezone
from .models import AICache, AIRateLimit
from typing import Dict, Any, Optional, List, Union # Added Union for flexible types

logger = logging.getLogger(__name__) # <-- INITIALIZED LOGGER

# --- Caching and Hashing ---

def calculate_request_hash(prompt: str, model: str, params: Dict[str, Any]) -> str:
    """Calculate hash for caching AI responses based on input parameters."""
    cache_key = f"{prompt}_{model}_{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(cache_key.encode('utf-8')).hexdigest()

def cache_ai_response(request_hash: str, prompt: str, response_text: str, model_used: str):
    """Cache AI responses to reduce API calls."""
    try:
        AICache.objects.create(
            request_hash=request_hash,
            prompt=prompt[:5000],   # Truncate prompt for storage
            response=response_text[:5000],  # Truncate response
            model_used=model_used
        )
    except Exception as e:
        logger.error(f"Cache failed for hash {request_hash}: {e}") # <-- IMPROVED LOGGING

def get_cached_response(request_hash: str) -> Optional[str]:
    """Get cached AI response if exists and not expired."""
    try:
        cached = AICache.objects.get(request_hash=request_hash)
        if not cached.is_expired():
            # Atomically update access count/time
            AICache.objects.filter(pk=cached.pk).update(
                access_count=cached.access_count + 1,
                last_accessed=timezone.now()
            )
            return cached.response
        # If expired, delete the old entry
        cached.delete()
        return None
    except AICache.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Cache retrieval failed for hash {request_hash}: {e}") # <-- IMPROVED LOGGING
    return None

# --- Token and Safety ---

def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
    if not text:
        return 0
    return len(text) // 4

def truncate_for_context(text: str, max_tokens: int = 4000) -> str: # <-- REDUCED DEFAULT TO 4000
    """
    Truncate text to fit within a sane context window (approx. 4 chars per token).
    The factor 3.5 is a common safety margin.
    """
    if not text:
        return ""
        
    # Use a more conservative 3.5 characters per token to be safe
    max_chars = int(max_tokens * 3.5) 
    
    if len(text) <= max_chars:
        return text
        
    return text[:max_chars] + "\n... [TRUNCATED for context window]" # <-- Added newline for clarity

def check_content_safety(text: str) -> bool:
    """Placeholder for content safety check (e.g., using Gemini moderation)."""
    return True

def format_ai_response(raw_response: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool, None]]:
    """Format AI response for frontend/logging."""
    # Ensure types are handled correctly for optional fields (like processing_time)
    return {
        'text': raw_response.get('text', ''),
        'model': raw_response.get('model', 'gemini-2.5-flash'),
        'prompt_tokens': raw_response.get('prompt_tokens', 0),
        'completion_tokens': raw_response.get('completion_tokens', 0),
        'total_tokens': raw_response.get('total_tokens', 0),
        'processing_time': raw_response.get('processing_time'),
        'success': raw_response.get('success', False),
    }

def get_user_rate_limit(user: Any) -> AIRateLimit:
    """Get or create the user's rate limit entry."""
    rate_limit, created = AIRateLimit.objects.get_or_create(user=user)
    
    # Only reset if the object wasn't just created and the time has passed
    if not created:
        rate_limit.reset_if_needed() 
        
    return rate_limit

# --- REMOVED: _prepare_gemini_content as it was incomplete and not used ---