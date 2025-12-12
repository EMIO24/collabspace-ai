from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Project, ProjectMember, ProjectActivity

# --- Helper Function for Activity Logging ---

def log_project_activity(project, user, action, description, metadata=None):
    """A reusable function to create an activity log entry."""
    if metadata is None:
        metadata = {}
    
    # Avoid creating logs if project is deleted or user is missing
    if not project or not user:
        return

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
    1. Ensures the Project owner is automatically added as a ProjectMember.
    2. Logs Project creation activity.
    """
    if created:
        # 1. Add owner as ProjectMember (Role: 'owner')
        # We use get_or_create to prevent race conditions
        ProjectMember.objects.get_or_create(
            project=instance,
            user=instance.owner,
            defaults={'role': 'owner', 'added_by': instance.owner}
        )
        
        # 2. Log creation activity
        log_project_activity(
            project=instance,
            user=instance.owner,
            action='created',
            description=f'Project "{instance.name}" was created.',
        )

# --- Project Member Signals ---

@receiver(post_save, sender=ProjectMember)
def handle_project_member_save(sender, instance, created, **kwargs):
    """
    1. Triggers Project member count update.
    2. Logs member addition activity.
    """
    # 1. Update counts on the Project model
    if hasattr(instance.project, 'update_counts'):
        instance.project.update_counts()

    # 2. Log member addition
    if created:
        # Prevent double-logging the initial owner creation
        is_initial_owner = (instance.role == 'owner' and 
                            instance.user == instance.project.owner and 
                            instance.project.members.count() <= 1)
        
        if not is_initial_owner:
            performer = instance.added_by or instance.project.owner
            log_project_activity(
                project=instance.project,
                user=performer,
                action='member_added',
                description=f'{instance.user.get_full_name() or instance.user.email} was added as {instance.role}.',
                metadata={'user_id': str(instance.user.id), 'role': instance.role}
            )

@receiver(post_delete, sender=ProjectMember)
def handle_project_member_delete(sender, instance, **kwargs):
    """
    1. Triggers Project member count update.
    2. Logs member removal activity.
    """
    # 1. Update counts on the Project model
    if hasattr(instance.project, 'update_counts'):
        instance.project.update_counts()

    # 2. Log member removal
    # We fallback to project owner as the 'actor' since the member is gone
    log_project_activity(
        project=instance.project,
        user=instance.project.owner,
        action='member_removed',
        description=f'{instance.user.get_full_name() or instance.user.email} was removed from the project.',
        metadata={'user_id': str(instance.user.id)}
    )