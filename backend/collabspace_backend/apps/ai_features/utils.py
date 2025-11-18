import hashlib
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Mock cache implementation (in a real scenario, this would use Redis or Django cache)
_RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}

# --- Gemini Model Pricing (Mock Data as of late 2024 for example) ---
# NOTE: Pricing is token-based (input vs. output) or duration-based (audio/video).
GEMINI_PRICING: Dict[str, Dict[str, float]] = {
    # Text generation pricing (per 1M tokens)
    "gemini-2.5-flash": {
        "input_cost": 0.0000005,  # $0.50 per 1M tokens
        "output_cost": 0.0000015, # $1.50 per 1M tokens
    },
    "gemini-2.5-pro": {
        "input_cost": 0.0000035, # $3.50 per 1M tokens
        "output_cost": 0.0000070, # $7.00 per 1M tokens
    },
    # Audio/STT pricing (per minute of audio)
    "audio-stt-standard": {
        "cost_per_minute": 0.006, # Example: $0.006 per minute
    }
}

def calculate_ai_cost(input_tokens: int = 0, output_tokens: int = 0, model_name: str = 'unknown', audio_minutes: float = 0.0) -> float:
    """
    Calculate the estimated cost in USD based on token usage, audio duration, and model.
    
    Args:
        input_tokens: Number of prompt tokens used.
        output_tokens: Number of response tokens used.
        model_name: The name of the model used (e.g., 'gemini-2.5-flash' or 'audio-stt-standard').
        audio_minutes: The duration of audio processed in minutes.
        
    Returns:
        The total estimated cost in USD.
    """
    model_name_lower = model_name.lower()
    total_cost = 0.0

    # 1. Token-based cost (for text generation/chat/summary)
    if input_tokens > 0 or output_tokens > 0:
        pricing = GEMINI_PRICING.get(model_name_lower)
        if pricing and "input_cost" in pricing:
            input_cost = input_tokens * pricing["input_cost"]
            output_cost = output_tokens * pricing["output_cost"]
            total_cost += input_cost + output_cost
        else:
            logger.warning(f"Token pricing not found for model: {model_name}. Using default minimum cost.")
            total_cost += 0.0000001
            
    # 2. Audio/Duration-based cost (for transcription/STT)
    if audio_minutes > 0.0:
        stt_pricing = GEMINI_PRICING.get("audio-stt-standard")
        if stt_pricing and "cost_per_minute" in stt_pricing:
            total_cost += audio_minutes * stt_pricing["cost_per_minute"]
        else:
            logger.error("STT pricing missing in GEMINI_PRICING.")

    return total_cost

def check_content_safety(text: str) -> bool:
    """
    Check text for harmful content using a mock or simple implementation.
    """
    # Simple keyword check for demonstration purposes
    unsafe_keywords = ["violence", "hate speech", "illegal activity"]
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in unsafe_keywords):
        return False
        
    return True

def format_ai_response(raw_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw AI response data into a cleaner, standardized structure for the frontend.
    """
    formatted_data = {
        "output_text": raw_response.get("text", raw_response.get("transcript", "No text content found.")),
        "model_used": raw_response.get("model", "unknown"),
        "is_safe": check_content_safety(raw_response.get("text", "")),
        "citation_sources": raw_response.get("sources", []),
        "usage_metadata": raw_response.get("usage_metadata", {})
    }
    return formatted_data

def cache_ai_response(request_hash: str, response: Dict[str, Any], ttl_seconds: int = 3600) -> None:
    """
    Cache AI responses to reduce redundant API calls for identical requests.
    """
    _RESPONSE_CACHE[request_hash] = {
        "response": response,
        "expires_at": time.time() + ttl_seconds
    }

def get_cached_response(request_hash: str) -> Optional[Dict[str, Any]]:
    """
    Get cached AI response if it exists and is not expired.
    """
    cache_entry = _RESPONSE_CACHE.get(request_hash)
    
    if cache_entry:
        if time.time() < cache_entry["expires_at"]:
            return cache_entry["response"]
        else:
            # Cache expired, clear it
            del _RESPONSE_CACHE[request_hash]
            
    return None

def generate_request_hash(payload: Dict[str, Any]) -> str:
    """
    Generates a unique, deterministic hash for a given AI request payload.
    """
    # Ensure stable dictionary order before hashing
    sorted_payload = str(sorted(payload.items()))
    return hashlib.sha256(sorted_payload.encode('utf-8')).hexdigest()