import time
import logging
from typing import Any, Dict, List, Optional
from google import genai
from google.genai.errors import ResourceExhausted, DeadlineExceeded, APIError

# --- CollabSpace Placeholder Imports ---
# Assuming these are defined elsewhere
class User:
    def __init__(self, id: int, email: str):
        self.id = id
        self.email = email
class settings:
    # Example settings - replace with actual config
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
    GEMINI_MODEL = "gemini-2.5-flash"
    OPENAI_MODEL = "gpt-4-turbo"
    ANTHROPIC_MODEL = "claude-3-sonnet"
# ---------------------------------------

# Import the new rate limit handler
from .rate_limit_handler import RateLimitHandler 

logger = logging.getLogger(__name__)

# Basic public pricing for Gemini 2.5 Flash (as of the search results)
# These values should be regularly checked and updated from Google's official pricing page.
# Prices are per 1 Million tokens (Input/Output).
GEMINI_FLASH_INPUT_PRICE_PER_M_TOKENS = 0.10  # USD
GEMINI_FLASH_OUTPUT_PRICE_PER_M_TOKENS = 0.40 # USD

class BaseAIService:
    """Base class for AI service providers with core utility methods."""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 30 # seconds
        self.rate_limit_handler = RateLimitHandler()
        
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text (Placeholder, implemented in subclasses)."""
        raise NotImplementedError("Subclasses must implement count_tokens")
        
    def handle_rate_limit(self, user: User) -> bool:
        """Check and enforce rate limits for a user."""
        user_key = f"user_{user.id}"
        return self.rate_limit_handler.check_and_enforce(user_key)
        
    def track_usage(self, user: User, input_tokens: int, output_tokens: int, cost: float, model: str):
        """Track AI usage for billing (Placeholder - log for now)."""
        # In a real application, this would write to a database/billing service
        total_tokens = input_tokens + output_tokens
        logger.info(
            f"USAGE: User {user.id} | Model: {model} | Input: {input_tokens} | Output: {output_tokens} | Total: {total_tokens} | Cost: ${cost:.6f}"
        )
        # TODO: Implement actual database tracking and cost attribution
        
    def handle_error(self, error: Exception, attempt: int) -> bool:
        """
        Handle API errors gracefully.
        :return: True if the request should be retried, False otherwise.
        """
        if isinstance(error, ResourceExhausted):
            logger.warning(f"Rate Limit Exceeded (429) on attempt {attempt}: {error}")
            # Do not retry immediately; rely on internal rate limiter or raise
            if attempt < self.max_retries:
                 # Exponential backoff on API's 429
                time.sleep(2 ** attempt)
                return True
            return False
            
        if isinstance(error, DeadlineExceeded):
            logger.error(f"Timeout (504) on attempt {attempt}: {error}")
            if attempt < self.max_retries:
                time.sleep(1) # Small linear backoff for transient timeouts
                return True
            return False
            
        if isinstance(error, APIError):
            logger.error(f"Gemini API Error (non-retryable): {error}")
            return False # Non-transient API errors are usually not worth retrying
            
        logger.error(f"Unexpected Error on attempt {attempt}: {type(error).__name__}: {error}")
        return False