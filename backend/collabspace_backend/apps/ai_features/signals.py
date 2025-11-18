from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AIUsage, AIRateLimit
from .tasks import send_quota_warning_email


@receiver(post_save, sender=AIUsage)
def track_ai_usage(sender, instance: AIUsage, created: bool, **kwargs):
    """Update rate limits when a successful AI request is logged."""
    if created and instance.success:
        try:
            # Get or create the rate limit model for the user
            rate_limit, _ = AIRateLimit.objects.get_or_create(user=instance.user)
            # This method handles the per-minute and daily increment
            rate_limit.increment_usage(instance.total_tokens)
        except Exception as e:
            # Log this error silently in production
            print(f"Error tracking usage for {instance.user.username}: {e}")

@receiver(post_save, sender=AIUsage)
def check_and_send_quota_warning(sender, instance: AIUsage, created: bool, **kwargs):
    """Send warning when approaching quota."""
    if created and instance.success:
        try:
            rate_limit = AIRateLimit.objects.get(user=instance.user)
            
            # Check if 90% of the daily request limit is reached
            daily_limit = rate_limit.daily_limit
            if daily_limit != -1 and rate_limit.requests_today >= daily_limit * 0.9:
                # Use Celery to send the email asynchronously
                send_quota_warning_email.delay(instance.user.id)
                
            # Check token limit as well
            tokens_limit = rate_limit.tokens_limit_day
            if rate_limit.tokens_today >= tokens_limit * 0.9:
                send_quota_warning_email.delay(instance.user.id)
                
        except AIRateLimit.DoesNotExist:
            pass # Ignore if rate limit entry doesn't exist yet