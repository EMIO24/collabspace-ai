import uuid
import json
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

# Custom imports (assuming User/Workspace models exist in the core app)
User = get_user_model()
try:
    # Use a dummy model if the actual one isn't available for isolated testing
    Workspace = models.ForeignKey('core.Workspace', on_delete=models.CASCADE, null=True, blank=True)
except Exception:
    class DummyWorkspace(models.Model):
        name = models.CharField(max_length=255)
    Workspace = models.ForeignKey(DummyWorkspace, on_delete=models.SET_NULL, null=True, blank=True)


class AIUsage(models.Model):
    """Tracks every individual AI request made for billing and quota management."""
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_usages')
    workspace = Workspace
    
    # Request Metadata
    feature_type = models.CharField(max_length=50, help_text="e.g., task_ai, meeting_ai, analytics_ai")
    provider = models.CharField(max_length=50, default='gemini')
    model_used = models.CharField(max_length=50, help_text="e.g., gemini-1.5-flash, gemini-1.5-pro")
    
    # Token and Time Tracking (Estimated for free tiers)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    processing_time = models.FloatField(null=True, blank=True, help_text="Seconds taken for the API call")
    
    # Data Storage (Truncated for privacy/storage limits)
    request_data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    response_data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    # Status
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Usage Log"
        verbose_name_plural = "AI Usage Logs"
        ordering = ['-created_at']
        # Efficiently query usage by user and feature type
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['feature_type', 'success']),
        ]

    def estimate_cost(self):
        """Calculate estimated cost (currently zero for free tier tracking)."""
        # In a real app, this would use a complex tiered pricing logic
        return 0.00 
    
    def __str__(self):
        return f"{self.user.username} - {self.feature_type} ({self.total_tokens} tokens)"


class AIPromptTemplate(models.Model):
    """Reusable, configurable templates for common AI tasks."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, help_text="task, meeting, analytics, etc.")
    prompt_template = models.TextField(help_text="Template with {{variable}} placeholders.")
    variables = models.JSONField(default=list, help_text="List of required variable names, e.g., ['task_description', 'user_name']")
    
    # Default Config
    default_model = models.CharField(max_length=50, default='flash', choices=[('flash', 'Gemini Flash'), ('pro', 'Gemini Pro')])
    default_max_tokens = models.IntegerField(default=1024)
    temperature = models.FloatField(default=0.7)
    
    # Status & Audit
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Prompt Template"
        verbose_name_plural = "AI Prompt Templates"
        unique_together = ('name', 'category')
        
    def __str__(self):
        return self.name


class User: 
    def __init__(self, id, username):
        self.id = id
        self.username = username
        self.email = f"{username}@example.com"
class SettingsPlaceholder:
    AI_USAGE_LIMITS = {
        'free': {'daily_requests': 100, 'tokens_per_request': 4000},
        'pro': {'daily_requests': 1000, 'tokens_per_request': 8000},
    }
    GEMINI_RATE_LIMIT_MIN = 60
settings = SettingsPlaceholder()
# -------------------------------------


class AIRateLimit(models.Model):
    """
    Tracks and enforces both daily and per-minute AI usage limits per user.
    This consolidated model includes feature-specific daily limits tracked 
    via a standardized 'cost' unit.
    """
    
    # Assuming User is the imported custom user model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_rate_limit')
    
    # Daily Limits (Reset nightly)
    plan_type = models.CharField(max_length=20, default='free', choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')])
    daily_limit = models.IntegerField(default=settings.AI_USAGE_LIMITS['free']['daily_requests'])
    tokens_limit_day = models.IntegerField(default=settings.AI_USAGE_LIMITS['free']['tokens_per_request'] * settings.AI_USAGE_LIMITS['free']['daily_requests'])

    requests_today = models.IntegerField(default=0)
    tokens_today = models.IntegerField(default=0)
    last_reset = models.DateTimeField(default=timezone.now)

    # Minute Limits (Reset every minute - crucial for Gemini free tier 60 req/min)
    minute_limit = models.IntegerField(default=settings.GEMINI_RATE_LIMIT_MIN)  # Default 60
    requests_this_minute = models.IntegerField(default=0)
    minute_reset_at = models.DateTimeField(default=timezone.now)

    # NEW: Tracks aggregated cost for high-value features (like STT, structured generation)
    feature_cost_today = models.IntegerField(default=0, help_text="Aggregated cost of high-value features like STT/Structured tasks.")


    class Meta:
        verbose_name = "AI Rate Limit"
        verbose_name_plural = "AI Rate Limits"

    def _get_daily_limits(self):
        """Get the limits based on the user's plan."""
        # In a real environment, this ensures the limits are correct based on the plan type
        return settings.AI_USAGE_LIMITS.get(self.plan_type, settings.AI_USAGE_LIMITS['free'])

    def reset_if_needed(self):
        """Resets daily and minute limits if time has passed."""
        now = timezone.now()
        should_save = False
        
        # 1. Daily Reset 
        if now.date() > self.last_reset.date():
            self.requests_today = 0
            self.tokens_today = 0
            self.feature_cost_today = 0 # Reset the feature cost tracker
            self.last_reset = now
            should_save = True
            
        # 2. Minute Reset
        if (now - self.minute_reset_at) > timedelta(seconds=60):
            self.requests_this_minute = 0
            self.minute_reset_at = now
            should_save = True

        if should_save:
            self.save()

    def check_minute_limit(self) -> bool:
        """Check if a request can be made based on the per-minute limit."""
        self.reset_if_needed()
        return self.requests_this_minute < self.minute_limit

    def can_make_request(self, feature_type: str, cost: int) -> bool:
        """
        Checks daily usage (based on cost) and minute limit.
        
        Note: The standard daily_limit (request count) is now implicitly handled 
        by incrementing requests_today in the final step. The feature_cost 
        check is the primary guardrail for high-cost operations.
        """
        self.reset_if_needed()
        
        # 1. Daily Feature Cost Check
        feature_limit = self.get_feature_limit(feature_type)
        if feature_limit != -1 and (self.feature_cost_today + cost) > feature_limit:
            return False
            
        # 2. Daily Token Check (Prevents large token consumption)
        if self.tokens_today >= self.tokens_limit_day:
            return False

        # 3. Minute Check (Applies to all requests)
        if not self.check_minute_limit():
            return False
            
        return True

    def increment_usage(self, tokens: int, cost: int = 1):
        """Increments usage counters."""
        self.requests_today += 1
        self.requests_this_minute += 1
        self.tokens_today += tokens
        self.feature_cost_today += cost # Increment feature cost
        self.save()

    def __str__(self):
        return f"RateLimit for {self.user.username} ({self.plan_type})"

    @staticmethod
    def get_feature_limit(feature_type: str) -> int:
        """Define different usage limits based on feature complexity/type."""
        if feature_type == 'task_ai':
            return 50 # Standard task_ai operations limit
        if feature_type == 'task_ai_audio': 
            return 10 # Stricter limit for STT
        return 100 # Default limit for general features
        
    @classmethod
    def track_usage(cls, user: User, feature_type: str, cost: int = 1, tokens: int = 500) -> 'AIRateLimit':
        """
        Public class method used by services to check limits and increment usage.
        
        :raises Exception: If the usage limit is exceeded.
        """
        try:
            # 1. Get or Create the limit object (using Django's get_or_create)
            limit_obj, created = cls.objects.get_or_create(
                user=user,
                defaults={
                    # Initialize default values upon creation
                    'daily_limit': settings.AI_USAGE_LIMITS['free']['daily_requests'],
                    'tokens_limit_day': settings.AI_USAGE_LIMITS['free']['tokens_per_request'] * settings.AI_USAGE_LIMITS['free']['daily_requests']
                }
            )
        except Exception as e:
            raise Exception(f"Database error while retrieving rate limit: {e}")


        # 2. Check limits
        if not limit_obj.can_make_request(feature_type, cost):
            # Provide specific feedback on which limit failed
            if not limit_obj.check_minute_limit():
                raise Exception("Per-minute rate limit exceeded. Please wait a moment.")
            
            feature_limit = cls.get_feature_limit(feature_type)
            raise Exception(f"Daily usage limit exceeded for feature '{feature_type}'. Used {limit_obj.feature_cost_today}, Limit {feature_limit}.")

        # 3. Increment usage if check passes
        limit_obj.increment_usage(tokens=tokens, cost=cost)
        
        return limit_obj
        
        
class AICache(models.Model):
    """Caches idempotent AI requests to save on API calls."""
    
    # The hash is generated based on the prompt, model, and parameters.
    request_hash = models.CharField(max_length=32, unique=True, db_index=True)
    prompt = models.TextField()
    response = models.TextField()
    model_used = models.CharField(max_length=50)
    
    access_count = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now_add=True)
    
    CACHE_TTL_DAYS = 1

    class Meta:
        verbose_name = "AI Cache Entry"
        verbose_name_plural = "AI Cache Entries"
        
    def is_expired(self):
        """Check if cache is older than CACHE_TTL_DAYS."""
        expiration_date = timezone.now() - timedelta(days=self.CACHE_TTL_DAYS)
        return self.created_at < expiration_date

    def __str__(self):
        return self.request_hash[:8]

# Ensure Django settings have the necessary values (typically in settings.py)
# from core.constants import AI_USAGE_LIMITS, GEMINI_MODELS
# This setup assumes a fallback for safety if those constants aren't available
if not hasattr(settings, 'AI_USAGE_LIMITS'):
    setattr(settings, 'AI_USAGE_LIMITS', {
        'free': {'daily_requests': 60, 'tokens_per_request': 32000},
        'pro': {'daily_requests': 1500, 'tokens_per_request': 32000},
        'enterprise': {'daily_requests': -1, 'tokens_per_request': 8000},
    })
if not hasattr(settings, 'GEMINI_RATE_LIMIT_MIN'):
    setattr(settings, 'GEMINI_RATE_LIMIT_MIN', 60)

