from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def send_daily_digest():
    """Send daily notification digest to users who prefer it"""
    from .models import Notification, NotificationPreference
    from .services import NotificationService
    
    # Filter users whose email frequency is set to 'daily_digest'
    users_with_daily_digest = NotificationPreference.objects.filter(
        email_enabled=True, 
        email_frequency='daily_digest'
    ).select_related('user')

    cutoff_time = timezone.now() - timedelta(days=1)
    
    for pref in users_with_daily_digest:
        # Get all unread notifications from the last 24 hours
        notifications = Notification.objects.filter(
            user=pref.user,
            is_read=False,
            created_at__gte=cutoff_time
        ).order_by('-created_at') # Order for digest presentation
        
        if notifications.exists():
            # Use the NotificationService to send the email
            # Note: The send_email method has internal checks for quiet hours/frequency
            # but for a scheduled digest, we bypass the frequency check by using a dedicated task.
            # We explicitly need a modified send_email for digests or rely on the task logic.
            
            # --- Simplified logic for digest (requires context adjustment) ---
            # Re-implementing simplified digest send to skip the 'instant' check in services.py
            
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            context = {'notifications': notifications, 'user': pref.user}
            html_message = render_to_string('notifications/daily_digest.html', context)
            
            try:
                send_mail(
                    subject="Your Daily Notification Digest",
                    message='',
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[pref.user.email],
                    fail_silently=False
                )
            except Exception as e:
                # Log error in a real app
                # print(f"Error sending daily digest to {pref.user.username}: {e}")
                pass
            
            # OPTIONAL: Mark included notifications as read after sending the digest
            # notifications.update(is_read=True, read_at=timezone.now())


@shared_task
def cleanup_old_notifications():
    """Delete old read notifications (>30 days)"""
    from .models import Notification
    
    # Calculate the cutoff date (30 days ago)
    cutoff_date = timezone.now() - timedelta(days=30)
    
    # Delete all notifications that are read AND were read before the cutoff date
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        read_at__lt=cutoff_date
    ).delete()
    
    # print(f"Cleaned up {deleted_count} old read notifications.")
    return f"Cleaned up {deleted_count} old read notifications."