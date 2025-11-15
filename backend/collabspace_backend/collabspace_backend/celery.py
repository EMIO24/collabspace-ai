"""
Celery configuration for CollabSpace AI.

This module sets up Celery for asynchronous task processing.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collabspace_backend.settings')

# Create Celery app
app = Celery('collabspace_backend')

# Load configuration from Django settings with 'CELERY' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')


# ==============================================================================
# PERIODIC TASKS (Celery Beat Schedule)
# ==============================================================================

app.conf.beat_schedule = {
    # Clean up expired tokens every day at 2 AM
    'cleanup-expired-tokens': {
        'task': 'apps.authentication.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Send daily digest notifications at 9 AM
    'send-daily-digest': {
        'task': 'apps.notifications.tasks.send_daily_digest',
        'schedule': crontab(hour=9, minute=0),
    },
    
    # Clean up old notifications (older than 30 days) weekly
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(day_of_week=1, hour=3, minute=0),
    },
    
    # Update AI usage statistics every hour
    'update-ai-usage-stats': {
        'task': 'apps.ai_features.tasks.update_usage_statistics',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
    
    # Generate workspace analytics every 6 hours
    'generate-workspace-analytics': {
        'task': 'apps.analytics.tasks.generate_workspace_analytics',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}

# ==============================================================================
# CELERY TASK CONFIGURATIONS
# ==============================================================================

app.conf.task_routes = {
    # AI tasks - high priority queue
    'apps.ai_features.tasks.*': {'queue': 'ai_tasks'},
    
    # Email tasks - separate queue
    'apps.notifications.tasks.send_email': {'queue': 'emails'},
    
    # Analytics - low priority queue
    'apps.analytics.tasks.*': {'queue': 'analytics'},
    
    # Default queue for other tasks
    '*': {'queue': 'default'},
}

# Task execution settings
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
app.conf.task_reject_on_worker_lost = True

# Result backend settings
app.conf.result_expires = 3600  # Results expire after 1 hour
app.conf.result_persistent = True