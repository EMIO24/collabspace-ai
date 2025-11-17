from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Project, ProjectMember, ProjectActivity

# --- Helper Function for Activity Logging ---

def log_project_activity(project, user, action, description, metadata=None):
    """A reusable function to create an activity log entry."""
    if metadata is None:
        metadata = {}
    
    ProjectActivity.objects.create(
        project=project,
        user=user,
        action=action,
        description=description,
        metadata=metadata
    )

# --- Project Signals ---

@receiver(post_save, sender=Project)
def handle_project_save(sender, instance, created, **kwargs):
    """
    1. Ensures the Project owner is automatically added as a ProjectMember (Owner role).
    2. Logs Project creation activity.
    3. Handles status change activity logs.
    """
    if created:
        # 1. Add owner as ProjectMember (Role: 'owner')
        ProjectMember.objects.get_or_create(
            project=instance,
            user=instance.owner,
            defaults={'role': 'owner'}
        )
        
        # 2. Log creation activity
        log_project_activity(
            project=instance,
            user=instance.owner,
            action='created',
            description=f'Project "{instance.name}" was created.',
        )
        
    # 3. Log status changes (only check if not created)
    elif not created:
        # Check if status has changed (requires fetching old data, using update_fields in save is better)
        # Assuming the caller updates status explicitly and this signal is for general activity,
        # we'll log major changes if we have access to the old instance.
        # For simplicity and robust signal handling, we'll only log updates in dedicated methods 
        # (like archive(), complete()) or rely on pre_save for comparisons if necessary.

        pass


# --- Project Member Signals ---

@receiver(post_save, sender=ProjectMember)
def handle_project_member_save(sender, instance, created, **kwargs):
    """
    1. Triggers Project count update.
    2. Logs member addition activity.
    """
    # 1. Trigger project count update on member change
    instance.project.update_counts()

    # 2. Log member addition
    if created:
        # Prevent logging for the initial owner creation handled by the Project signal
        if instance.role != 'owner' or ProjectMember.objects.filter(project=instance.project).count() > 1:
            log_project_activity(
                project=instance.project,
                user=instance.added_by or instance.project.owner, # Assume added_by if available
                action='member_added',
                description=f'User {instance.user.email} was added as a {instance.role} to the project.',
                metadata={'user_id': str(instance.user.id), 'role': instance.role}
            )

@receiver(post_delete, sender=ProjectMember)
def handle_project_member_delete(sender, instance, **kwargs):
    """
    1. Triggers Project count update.
    2. Logs member removal activity.
    """
    # 1. Trigger project count update on member change
    instance.project.update_counts()

    # 2. Log member removal
    # NOTE: In a real app, you might want the user *performing* the deletion to be logged, 
    # but that user is not easily accessible here. We log the removed user.
    log_project_activity(
        project=instance.project,
        user=instance.project.owner, # Fallback to owner as the log initiator
        action='member_removed',
        description=f'User {instance.user.email} was removed from the project.',
        metadata={'user_id': str(instance.user.id)}
    )

# NOTE: When the Task model is added, you'll need additional signals on Task 
# (post_save/post_delete) to call Project.update_counts() for task metrics.