import json
import time
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from google.generativeai.errors import APIError

# Local Imports
from .services.gemini_service import GeminiService
from .services.task_ai import TaskAIService
from .services.meeting_ai import MeetingAIService
from .services.analytics_ai import AnalyticsAIService
from .models import AIUsage, AICache, AIRateLimit

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def process_ai_request_async(self, user_id: int, feature_type: str, request_data: Dict[str, Any]):
    """Process a generic AI request asynchronously with error handling and backoff."""
    try:
        user = User.objects.get(pk=user_id)
        
        # Dispatch based on feature type
        service_map = {
            'task_summarize': TaskAIService().summarize_task,
            'task_breakdown': TaskAIService().break_down_task,
            'meeting_summarize': MeetingAIService().summarize_meeting,
            # Add other features here
        }
        
        # Use a wrapper to call the method, passing user and data
        if feature_type in service_map:
            result = service_map[feature_type](user, **request_data)
            # Log successful processing and return result ID/data
            return {'status': 'SUCCESS', 'result': result}
        else:
            raise ValueError(f"Unknown feature type: {feature_type}")
            
    except User.DoesNotExist:
        return {'status': 'FAILED', 'error': 'User not found.'}
    except APIError as e:
        # Retry on API failure with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
    except Exception as e:
        # Final failure state after max retries or non-retriable error
        return {'status': 'FAILED', 'error': str(e)}


@shared_task
def generate_project_forecast(project_id: uuid.UUID):
    """Generate AI project forecast in the background."""
    # Placeholder: Fetch User from Project model, get Project data
    service = AnalyticsAIService()
    dummy_user = User.objects.first() # Use a system user or project owner
    project_data = f"Data for project {project_id}: Scope=1000, Velocity=50."
    
    try:
        forecast = service.forecast_completion(dummy_user, project_data)
        # TODO: Save to cache/DB and send notification
        print(f"Forecast for {project_id}: {forecast}")
    except Exception as e:
        print(f"Failed to generate forecast for {project_id}: {e}")


@shared_task
def batch_summarize_tasks(task_ids: List[uuid.UUID]):
    """Batch summarize multiple tasks, respecting rate limits implicitly."""
    service = TaskAIService()
    dummy_user = User.objects.first() # Use a system user or request owner
    
    for task_id in task_ids:
        # Placeholder: Fetch Task description
        task_description = f"Description for Task {task_id}"
        
        try:
            # The service call handles rate limit checks and retries internally
            summary = service.summarize_task(dummy_user, task_description)
            # TODO: Save summary back to the Task model
            print(f"Summary for {task_id}: {summary}")
        except APIError as e:
            # Stop batch if hitting persistent API errors
            print(f"Batch processing stopped due to API error: {e}")
            break
        except Exception as e:
            print(f"Failed to summarize task {task_id}: {e}")


@shared_task
def update_usage_statistics():
    """Update AI usage stats and user quotas (hourly)."""
    # This task primarily serves as a trigger for administrative actions
    # The actual quota update is handled by the AIUsage signal
    
    # 1. Check for users approaching limits
    for rate_limit in AIRateLimit.objects.filter(requests_today__gte=models.F('daily_limit') * 0.9):
        # Trigger quota warning email if not sent recently
        send_quota_warning_email.delay(rate_limit.user.id)


@shared_task
def cleanup_old_ai_logs():
    """Cleanup AI logs and cache entries older than 90 days."""
    cutoff_date = timezone.now() - timedelta(days=90)
    
    # Clean usage logs
    deleted_usage, _ = AIUsage.objects.filter(created_at__lt=cutoff_date).delete()
    print(f"Cleaned up {deleted_usage} old AI usage logs.")
    
    # Clean expired cache entries (using the model's check)
    expired_cache = AICache.objects.filter(created_at__lt=cutoff_date).delete()
    print(f"Cleaned up {expired_cache} expired AI cache entries.")


@shared_task
def send_quota_warning_email(user_id: int):
    """Send email when user approaches quota limit."""
    try:
        user = User.objects.get(pk=user_id)
        # NOTE: This should be configured with Django's email backend
        send_mail(
            subject='AI Usage Quota Warning',
            message=f"Hi {user.username},\n\nYou are approaching your daily AI usage limit. Consider upgrading your plan or reducing usage.",
            from_email='noreply@collabspace.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
    except User.DoesNotExist:
        pass


@shared_task
def reset_rate_limits():
    """Reset daily rate limits (runs at midnight)."""
    now = timezone.now()
    # Reset daily counters
    AIRateLimit.objects.filter(last_reset__lt=now.date()).update(
        requests_today=0,
        tokens_today=0,
        last_reset=now
    )
    # Reset minute counters (in case the hourly update missed it)
    AIRateLimit.objects.all().update(
        requests_this_minute=0
    )
    print("Daily and minute rate limits reset.")


@shared_task
def warm_up_gemini_connection():
    """Keep Gemini connection warm (runs every 5 minutes)."""
    service = GeminiService()
    dummy_user = User.objects.first() # Use a system user
    
    try:
        # Make a lightweight, non-logged, low-token test request
        # NOTE: Using a custom method here is better to avoid logging/rate checking
        # For simplicity, we use generate_completion with a very low token count
        # In a real app, you would use client.models.generate_content directly without tracking.
        service.generate_completion(dummy_user, "hi", "warmup", max_tokens=1)
        print("Gemini connection warmed up.")
    except Exception as e:
        print(f"Gemini warmup failed: {e}")
