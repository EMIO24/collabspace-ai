from typing import Optional, Dict, Any, Union
from django.conf import settings
from apps.ai_features.models import AIRateLimit, AIUsage


class BaseAIService:
    """Base class for all AI services with common rate limiting and logging."""
    
    # Each service should define its feature type
    FEATURE_TYPE: str = 'general'
    
    def __init__(self):
        """Initialize the base service."""
        pass
    
    def handle_rate_limit(self, user: Any, feature_type: Optional[str] = None, cost: int = 1) -> bool:
        """
        Check if user can make a request based on rate limits.
        
        Args:
            user: The user making the request (Django User object or similar).
            feature_type: The type of feature being accessed (defaults to self.FEATURE_TYPE).
            cost: The cost/weight of this request (default 1).
            
        Returns:
            bool: True if request is allowed.
            
        Raises:
            Exception: If rate limit is exceeded (with descriptive message).
        """
        # Use the provided feature_type or fall back to the service's default
        if feature_type is None:
            feature_type = getattr(self, 'FEATURE_TYPE', 'general')
        
        # Get or create rate limit object
        rate_limit, _ = AIRateLimit.objects.get_or_create(user=user)
        
        # Check if request can be made
        if not rate_limit.can_make_request(feature_type=feature_type, cost=cost):
            # Provide specific feedback on which limit failed
            if not rate_limit.check_minute_limit():
                raise Exception("Per-minute rate limit exceeded. Please wait a moment.")
            
            feature_limit = AIRateLimit.get_feature_limit(feature_type)
            raise Exception(
                f"Daily usage limit exceeded for feature '{feature_type}'. "
                f"Used {rate_limit.feature_cost_today}, Limit {feature_limit}."
            )
        
        return True
    
    def log_usage(self, 
                  user: Any, 
                  feature_type: str, 
                  prompt_tokens: int, 
                  completion_tokens: int, 
                  workspace: Any, 
                  model_used: str = 'gemini-2.0-flash-exp', 
                  provider: str = 'gemini', 
                  success: bool = True, 
                  error_message: Optional[str] = None, 
                  processing_time: Optional[float] = None, 
                  request_data: Optional[Dict[str, Any]] = None, 
                  response_data: Optional[Dict[str, Any]] = None):
        """
        Log AI usage to the database.
        """
        total_tokens = prompt_tokens + completion_tokens
        
        AIUsage.objects.create(
            user=user,
            workspace=workspace,  # Required field
            feature_type=feature_type,
            provider=provider,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            processing_time=processing_time,
            request_data=request_data,
            response_data=response_data,
            success=success,
            error_message=error_message,
        ) 
           
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Simple estimation: ~4 characters per token for English text.
        
        Args:
            text: The text to estimate tokens for.
            
        Returns:
            int: Estimated token count.
        """
        if not text:
            return 0
        return len(text) // 4