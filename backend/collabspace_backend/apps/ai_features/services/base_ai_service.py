import time
import logging
from typing import Any, Dict, List, Optional, Union
from google import genai
from google.genai.errors import ResourceExhaustedError, APIError, DeadlineExceededError
from rate_limit_handler import RateLimitHandler # Assume handler is accessible

logger = logging.getLogger(__name__)

# NOTE: Pricing is illustrative and should be updated based on current Google AI documentation (per 1M tokens)
GEMINI_COSTS = {
    "gemini-2.5-flash": {"input": 0.35, "output": 0.70},
    "gemini-2.5-pro": {"input": 3.50, "output": 7.00},
    "text-embedding-004": {"input": 0.10, "output": 0.0},
}

class BaseAIService:
    """Base class for AI service providers, providing common utility and error handling."""
    
    def __init__(self):
        self.max_retries = 3
        self.timeout = 30
        self.rate_limit_handler = RateLimitHandler() # Application-level rate limit
        self.FALLBACK_RESPONSE = settings.FALLBACK_RESPONSE

    def count_tokens(self, text: Union[str, List[Any]], model: str = settings.GEMINI_MODEL) -> int:
        """Count tokens in text (Placeholder - will be implemented in GeminiService)."""
        raise NotImplementedError("Token counting must be implemented by the concrete service.")

    def handle_rate_limit(self, user_id: str) -> bool:
        """Check and enforce application-level rate limits for a user."""
        return self.rate_limit_handler.check_and_increment(user_id)

    def calculate_cost(self, model: str, input_tokens: int = 0, output_tokens: int = 0) -> float:
        """Calculate AI usage cost in USD."""
        costs = GEMINI_COSTS.get(model, {"input": 0, "output": 0})
        # Costs are typically per 1,000,000 tokens
        input_cost = (input_tokens / 1_000_000) * costs['input']
        output_cost = (output_tokens / 1_000_000) * costs['output']
        return input_cost + output_cost

    def track_usage(self, user_id: str, model: str, input_tokens: int, output_tokens: int):
        """Track AI usage for billing (Placeholder - integrate with DB/Analytics)."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        logger.info(f"User {user_id} used {input_tokens} input, {output_tokens} output tokens on {model}. Cost: ${cost:.6f}")
        # Production: Save this record to a database table (e.g., UsageTracker)
        # UsageTracker.create(user_id=user_id, model=model, input_tokens=input_tokens, output_tokens=output_tokens, cost=cost)

    def handle_error(self, error: Exception, attempt: int) -> bool:
        """Handle API errors gracefully and determine if a retry is warranted."""
        should_retry = False
        
        if isinstance(error, ResourceExhaustedError):
            delay = 2 ** attempt # Exponential backoff for rate limit/quota
            logger.warning(f"Quota/Rate Limit exceeded. Retrying in {delay}s...")
            time.sleep(delay)
            should_retry = True
        elif isinstance(error, (APIError, DeadlineExceededError)):
            delay = 2 ** attempt
            logger.error(f"Transient connection/server error. Retrying in {delay}s: {error}")
            time.sleep(delay)
            should_retry = True
        else:
            logger.error(f"Non-retryable or unexpected error: {error}")
            should_retry = False
            
        return should_retry