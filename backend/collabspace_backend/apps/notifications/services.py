from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Notification, NotificationPreference
from django.core.exceptions import ImproperlyConfigured

# Ensure settings are properly configured for email
if not hasattr(settings, 'DEFAULT_FROM_EMAIL'):
    raise ImproperlyConfigured("DEFAULT_FROM_EMAIL must be set in settings.")

class NotificationService:
    """Centralized notification service"""
    
    @staticmethod
    def create_notification(user, notification_type, title, message, **kwargs):
        """Create in-app notification"""
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            action_url=kwargs.get('action_url'),
            related_object_type=kwargs.get('related_object_type'),
            related_object_id=kwargs.get('related_object_id'),
            priority=kwargs.get('priority', 'medium'),
            metadata=kwargs.get('metadata', {})
        )
        return notification

    @staticmethod
    def send_email(user, subject, template, context):
        """Send email notification"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        
        # Check overall channel preference and frequency
        if not prefs.email_enabled or prefs.email_frequency != 'instant':
            return False
            
        # Check quiet hours - apply only to instant emails
        if prefs.is_quiet_hours():
            return False
            
        html_message = render_to_string(template, context)
        
        try:
            send_mail(
                subject=subject,
                message='', # Plain text version can be added here
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )
            return True
        except Exception as e:
            # Log the error in a real application
            # print(f"Error sending email: {e}") 
            return False

    @staticmethod
    def send_push(user, title, body, data=None):
        """Send push notification (placeholder for Firebase/etc.)"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        
        if not prefs.push_enabled:
            return False
            
        # Check quiet hours
        if prefs.is_quiet_hours():
            return False

        # --- Implement Push Notification Logic Here ---
        # Example with a simple log/placeholder:
        # print(f"PUSH to {user.username}: Title='{title}', Body='{body}', Data={data}")
        
        # In a real app, integrate with FCM/APNS:
        # from firebase_admin.messaging import Message, Notification as FcmNotification, send
        # try:
        #     fcm_token = user.fcm_token # Assume user model has this field
        #     message = Message(
        #         notification=FcmNotification(title=title, body=body),
        #         data=data or {},
        #         token=fcm_token
        #     )
        #     response = send(message)
        #     return True
        # except Exception:
        #     return False
        
        # Placeholder success for completion
        return True


    @staticmethod
    def should_send(user, notification_type, channel):
        """
        Check if an INSTANT notification should be sent based on 
        channel-specific, type-specific preferences.
        
        Note: Email frequency (digest/never) and quiet hours are handled in send_email/send_push.
        """
        try:
            prefs = NotificationPreference.objects.get(user=user)
            return prefs.get_preference(notification_type, channel)
        except NotificationPreference.DoesNotExist:
            return True  # Default to sending

    @staticmethod
    def send_multi_channel(user, notification_type, data):
        """
        Send notification via all enabled channels.
        `data` must contain 'title' and 'message'.
        Optional keys: 'action_url', 'related_object_type', 'related_object_id', 'priority', 'metadata', 'email_template', 'context', 'push_data'.
        """
        if not user.is_active:
            return None # Don't send notifications to inactive users
            
        # Create in-app notification (always created regardless of preference)
        notification = NotificationService.create_notification(
            user=user,
            notification_type=notification_type,
            title=data['title'],
            message=data['message'],
            **data.get('kwargs', {})
        )

        # Send email if enabled for this type and channel/frequency is instant
        if NotificationService.should_send(user, notification_type, 'email'):
            NotificationService.send_email(
                user=user,
                subject=data['title'],
                # Default email template if not provided
                template=data.get('email_template', 'notifications/default.html'), 
                context=data.get('context', {'notification': notification})
            )
        
        # Send push if enabled for this type
        if NotificationService.should_send(user, notification_type, 'push'):
            NotificationService.send_push(
                user=user,
                title=data['title'],
                body=data['message'],
                data=data.get('push_data', {})
            )
            
        return notification