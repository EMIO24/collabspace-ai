import logging
from typing import Tuple, Optional

# Assume these classes/functions exist in the broader application
# Mock imports for demonstration
class User:
    def __init__(self, plan_type: str, id: str):
        self.plan_type = plan_type
        self.id = id

class AIUsageManager:
    """Mock class to simulate database interaction for usage tracking."""
    def get_daily_usage(self, user_id: str) -> int:
        # In a real app, this would query the AIUsage model for today's count
        # This currently returns 0 for demonstration purposes.
        return 0 

# Mock settings class
class Settings:
    RATE_LIMITS = {
        'FREE': 10,
        'PRO': 100,
        'ENTERPRISE': float('inf'),
    }
settings = Settings()

logger = logging.getLogger(__name__)


class HasAIAccess:
    """
    Custom permission to check AI feature access based on user plan and daily limits.
    
    Rate limits:
    - FREE: 10 calls/day
    - PRO: 100 calls/day
    - ENTERPRISE: Unlimited
    """
    def has_permission(self, request, view) -> Tuple[bool, Optional[int]]:
        """Checks if the user has access to the AI feature based on their plan."""
        # This assumes the user object is attached to the request (e.g., request.user in Django)
        user = request.user
        user_plan = user.plan_type.upper()
        
        limit = settings.RATE_LIMITS.get(user_plan, 0)

        if limit == float('inf'):
            # Enterprise has unlimited access
            return True, None

        usage_manager = AIUsageManager()
        current_usage = usage_manager.get_daily_usage(user.id)
        
        if current_usage >= limit:
            logger.warning(f"Rate limit exceeded for user {user.id} ({user_plan}): {current_usage}/{limit}")
            return False, limit
        
        # User is within limits
        return True, limit

# Attach the permission check function to the class for easy usage
HasAIAccess.has_permission = classmethod(HasAIAccess.has_permission)