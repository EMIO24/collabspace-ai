"""
CollabSpace AI - Tasks Module Signals
Signal handlers for task-related events and notifications.
"""

from django.db.models.signals import post_save, pre_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Task, TaskComment, TaskAttachment, TimeEntry, TaskDependency

User = get_user_model()


# =============================================================================
# 1. Project Statistics Update Signal
# =============================================================================

@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def update_project_stats(sender, instance, **kwargs):
    """
    Triggered whenever a Task is saved or deleted.
    Recalculates the parent Project's statistics (progress, task counts).
    """
    if instance.project:
        if hasattr(instance.project, 'update_statistics'):
            instance.project.update_statistics()


# =============================================================================
# 2. Existing Notification & Metadata Signals
# =============================================================================

@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    """
    Handle task pre-save operations.
    Track status changes and update metadata.
    """
    if instance.pk:
        try:
            old_task = Task.objects.get(pk=instance.pk)
            
            # Track status changes
            if old_task.status != instance.status:
                if not instance.metadata:
                    instance.metadata = {}
                
                # Initialize status history if not exists
                if 'status_history' not in instance.metadata:
                    instance.metadata['status_history'] = []
                
                # Add status change to history
                instance.metadata['status_history'].append({
                    'from': old_task.status,
                    'to': instance.status,
                    'changed_at': timezone.now().isoformat(),
                })
            
            # Track assignment changes
            if old_task.assigned_to != instance.assigned_to:
                if not instance.metadata:
                    instance.metadata = {}
                
                if 'assignment_history' not in instance.metadata:
                    instance.metadata['assignment_history'] = []
                
                # ✅ FIX: Convert UUIDs to strings before saving to JSON
                old_user_id = str(old_task.assigned_to.id) if old_task.assigned_to else None
                new_user_id = str(instance.assigned_to.id) if instance.assigned_to else None

                instance.metadata['assignment_history'].append({
                    'from': old_user_id,
                    'to': new_user_id,
                    'changed_at': timezone.now().isoformat(),
                })
        
        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    """
    Handle task post-save operations.
    Create notifications for relevant users.
    """
    from apps.notifications.models import Notification  # Avoid circular import
    
    if created:
        # Task created notification
        notification_data = {
            'type': 'task_created',
            'title': 'New Task Created',
            'message': f'Task "{instance.title}" has been created',
            'related_object_type': 'task',
            'related_object_id': instance.id,
            'action_url': f'/tasks/{instance.id}/',
        }
        
        # Notify project members
        if instance.project:
            project_members = instance.project.members.all()
            for member in project_members:
                if member.user != instance.created_by:
                    Notification.objects.create(
                        user=member.user,
                        **notification_data
                    )
    else:
        # Notify on assignment (handled in view or pre_save mostly, kept here for consistency if needed)
        pass


@receiver(post_save, sender=Task)
def task_status_changed(sender, instance, created, **kwargs):
    """
    Handle task status changes notifications.
    """
    if not created and instance.pk:
        from apps.notifications.models import Notification
        
        # If task is completed, notify collaborators
        if instance.status == Task.STATUS_DONE:
             collaborators = instance.get_collaborators()
             for collaborator in collaborators:
                 if collaborator not in [instance.assigned_to, instance.created_by]:
                     Notification.objects.create(
                         user=collaborator,
                         type='task_completed',
                         title='Task Completed',
                         message=f'Task "{instance.title}" has been completed',
                         related_object_type='task',
                         related_object_id=instance.id,
                         action_url=f'/tasks/{instance.id}/',
                     )


@receiver(post_save, sender=TaskComment)
def comment_created(sender, instance, created, **kwargs):
    """
    Handle comment creation.
    Notify task stakeholders about new comments.
    """
    if created:
        from apps.notifications.models import Notification
        
        task = instance.task
        
        # Notify assigned user
        if task.assigned_to and task.assigned_to != instance.user:
            Notification.objects.create(
                user=task.assigned_to,
                type='task_comment',
                title='New Comment on Task',
                message=f'{instance.user.username} commented on "{task.title}"',
                related_object_type='task',
                related_object_id=task.id,
                action_url=f'/tasks/{task.id}/#comment-{instance.id}',
            )
        
        # Notify task creator
        if task.created_by and task.created_by not in [instance.user, task.assigned_to]:
            Notification.objects.create(
                user=task.created_by,
                type='task_comment',
                title='New Comment on Task',
                message=f'{instance.user.username} commented on "{task.title}"',
                related_object_type='task',
                related_object_id=task.id,
                action_url=f'/tasks/{task.id}/#comment-{instance.id}',
            )
        
        # If it's a reply, notify parent comment author
        if instance.parent_comment:
            parent_author = instance.parent_comment.user
            if parent_author != instance.user:
                Notification.objects.create(
                    user=parent_author,
                    type='comment_reply',
                    title='Reply to Your Comment',
                    message=f'{instance.user.username} replied to your comment',
                    related_object_type='task',
                    related_object_id=task.id,
                    action_url=f'/tasks/{task.id}/#comment-{instance.id}',
                )


@receiver(m2m_changed, sender=TaskComment.mentions.through)
def comment_mentions_changed(sender, instance, action, pk_set, **kwargs):
    """
    Handle comment mentions.
    Notify mentioned users.
    """
    if action == 'post_add' and pk_set:
        from apps.notifications.models import Notification
        
        mentioned_users = User.objects.filter(pk__in=pk_set)
        task = instance.task
        
        for user in mentioned_users:
            if user != instance.user:
                Notification.objects.create(
                    user=user,
                    type='user_mentioned',
                    title='You Were Mentioned',
                    message=f'{instance.user.username} mentioned you in a comment on "{task.title}"',
                    related_object_type='task',
                    related_object_id=task.id,
                    action_url=f'/tasks/{task.id}/#comment-{instance.id}',
                )


@receiver(post_save, sender=TaskAttachment)
def attachment_uploaded(sender, instance, created, **kwargs):
    """
    Handle attachment upload.
    Notify task stakeholders about new attachments.
    """
    if created:
        from apps.notifications.models import Notification
        
        task = instance.task
        
        # Notify assigned user
        if task.assigned_to and task.assigned_to != instance.uploaded_by:
            Notification.objects.create(
                user=task.assigned_to,
                type='task_attachment',
                title='New Attachment Added',
                message=f'{instance.uploaded_by.username} added "{instance.file_name}" to "{task.title}"',
                related_object_type='task',
                related_object_id=task.id,
                action_url=f'/tasks/{task.id}/',
            )
        
        # Notify task creator
        if task.created_by and task.created_by not in [instance.uploaded_by, task.assigned_to]:
            Notification.objects.create(
                user=task.created_by,
                type='task_attachment',
                title='New Attachment Added',
                message=f'{instance.uploaded_by.username} added "{instance.file_name}" to "{task.title}"',
                related_object_type='task',
                related_object_id=task.id,
                action_url=f'/tasks/{task.id}/',
            )


@receiver(post_save, sender=TimeEntry)
def time_entry_logged(sender, instance, created, **kwargs):
    """
    Handle time entry logging.
    Update task metadata and notify if needed.
    """
    if created:
        task = instance.task
        
        # Update task metadata with time tracking info
        if not task.metadata:
            task.metadata = {}
        
        # ✅ FIX: Convert user ID to string
        user_id_str = str(instance.user.id)

        if 'time_tracking' not in task.metadata:
            task.metadata['time_tracking'] = {
                'last_logged': timezone.now().isoformat(),
                'last_logged_by': user_id_str,
                'total_entries': 1
            }
        else:
            task.metadata['time_tracking']['last_logged'] = timezone.now().isoformat()
            task.metadata['time_tracking']['last_logged_by'] = user_id_str
            task.metadata['time_tracking']['total_entries'] = task.time_entries.count()
        
        task.save(update_fields=['metadata'])
        
        # Notify if over estimated hours
        if task.estimated_hours:
            actual_hours = task.get_actual_hours()
            if actual_hours > task.estimated_hours:
                from apps.notifications.models import Notification
                
                # Notify task creator
                if task.created_by:
                    Notification.objects.create(
                        user=task.created_by,
                        type='task_over_estimate',
                        title='Task Over Estimate',
                        message=f'Task "{task.title}" has exceeded estimated hours ({actual_hours}h / {task.estimated_hours}h)',
                        related_object_type='task',
                        related_object_id=task.id,
                        action_url=f'/tasks/{task.id}/',
                    )


@receiver(post_save, sender=TaskDependency)
def dependency_created(sender, instance, created, **kwargs):
    """
    Handle dependency creation.
    Notify relevant users about task dependencies.
    """
    if created:
        from apps.notifications.models import Notification
        
        task = instance.task
        depends_on = instance.depends_on
        
        # Notify assigned user of dependent task
        if task.assigned_to:
            Notification.objects.create(
                user=task.assigned_to,
                type='task_dependency',
                title='Task Dependency Added',
                message=f'Task "{task.title}" now depends on "{depends_on.title}"',
                related_object_type='task',
                related_object_id=task.id,
                action_url=f'/tasks/{task.id}/',
            )
        
        # Notify assigned user of blocking task
        if depends_on.assigned_to and depends_on.assigned_to != task.assigned_to:
            Notification.objects.create(
                user=depends_on.assigned_to,
                type='task_blocks',
                title='Your Task Blocks Another',
                message=f'Task "{depends_on.title}" is blocking "{task.title}"',
                related_object_type='task',
                related_object_id=depends_on.id,
                action_url=f'/tasks/{depends_on.id}/',
            )


@receiver(post_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
    """
    Handle task deletion.
    Notify relevant users about task deletion.
    """
    from apps.notifications.models import Notification
    
    # Notify assigned user
    if instance.assigned_to:
        Notification.objects.create(
            user=instance.assigned_to,
            type='task_deleted',
            title='Task Deleted',
            message=f'Task "{instance.title}" has been deleted',
            related_object_type='project',
            related_object_id=instance.project.id,
            action_url=f'/projects/{instance.project.id}/tasks/',
        )
    
    # Notify task creator
    if instance.created_by and instance.created_by != instance.assigned_to:
        Notification.objects.create(
            user=instance.created_by,
            type='task_deleted',
            title='Task Deleted',
            message=f'Task "{instance.title}" has been deleted',
            related_object_type='project',
            related_object_id=instance.project.id,
            action_url=f'/projects/{instance.project.id}/tasks/',
        )


# Signal to handle task due date reminders
def check_task_due_dates():
    """
    Utility function to check for upcoming due dates.
    This should be called by a scheduled task (e.g., Celery beat).
    """
    from apps.notifications.models import Notification
    from datetime import timedelta
    
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    
    # Get tasks due tomorrow that are not completed
    tasks_due_tomorrow = Task.objects.filter(
        due_date__gte=tomorrow,
        due_date__lt=tomorrow + timedelta(days=1),
        status__in=['todo', 'in_progress', 'review'],
        is_active=True
    ).select_related('assigned_to', 'created_by')
    
    for task in tasks_due_tomorrow:
        # Notify assigned user
        if task.assigned_to:
            Notification.objects.get_or_create(
                user=task.assigned_to,
                type='task_due_soon',
                related_object_type='task',
                related_object_id=task.id,
                defaults={
                    'title': 'Task Due Tomorrow',
                    'message': f'Task "{task.title}" is due tomorrow',
                    'action_url': f'/tasks/{task.id}/',
                }
            )
        
        # Notify task creator
        if task.created_by and task.created_by != task.assigned_to:
            Notification.objects.get_or_create(
                user=task.created_by,
                type='task_due_soon',
                related_object_type='task',
                related_object_id=task.id,
                defaults={
                    'title': 'Task Due Tomorrow',
                    'message': f'Task "{task.title}" is due tomorrow',
                    'action_url': f'/tasks/{task.id}/',
                }
            )