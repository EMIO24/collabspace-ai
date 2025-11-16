from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

Workspace = apps.get_model("workspaces", "Workspace")
WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
WorkspaceInvitation = apps.get_model("workspaces", "WorkspaceInvitation")
User = apps.get_model(settings.AUTH_USER_MODEL.split(".")[0], settings.AUTH_USER_MODEL.split(".")[1]) if "." in settings.AUTH_USER_MODEL else apps.get_model("auth", "User")


@receiver(post_save, sender=Workspace)
def ensure_owner_membership(sender, instance: Workspace, created, **kwargs):
    """
    When a Workspace is created ensure the owner has a WorkspaceMember entry (owner role).
    This prevents owner from not being listed in members.
    """
    try:
        if created:
            WorkspaceMember.objects.get_or_create(
                workspace=instance,
                user=instance.owner,
                defaults={"role": "owner", "is_active": True},
            )
            # Update member count
            instance.member_count = WorkspaceMember.objects.filter(workspace=instance, is_active=True).count()
            instance.save(update_fields=["member_count"])
    except Exception:
        logger.exception("Error creating owner membership for workspace %s", getattr(instance, "pk", None))


@receiver(post_save, sender=WorkspaceMember)
def update_member_count_on_save(sender, instance: WorkspaceMember, created, **kwargs):
    """
    Update the parent workspace member_count whenever membership is added/updated.
    """
    try:
        workspace = instance.workspace
        workspace.member_count = WorkspaceMember.objects.filter(workspace=workspace, is_active=True).count()
        workspace.save(update_fields=["member_count"])
    except Exception:
        logger.exception("Failed to update member_count after member save for workspace %s", getattr(instance.workspace, "pk", None))


@receiver(post_delete, sender=WorkspaceMember)
def update_member_count_on_delete(sender, instance: WorkspaceMember, **kwargs):
    """
    Update the parent workspace member_count when a membership is deleted.
    """
    try:
        workspace = instance.workspace
        # If workspace deleted too, accessing workspace may raise; guard for that.
        if workspace:
            workspace.member_count = WorkspaceMember.objects.filter(workspace=workspace, is_active=True).count()
            workspace.save(update_fields=["member_count"])
    except Exception:
        logger.exception("Failed to update member_count after member delete for workspace %s", getattr(instance.workspace, "pk", None))


@receiver(post_save, sender=WorkspaceInvitation)
def send_invitation_email(sender, instance: WorkspaceInvitation, created, **kwargs):
    """
    When an invitation is created, attempt to send an email to the invitee.
    In production systems it's best to push to a task queue (Celery/RQ). Here we attempt
    to send directly while handling exceptions gracefully.
    """
    if not created:
        return

    try:
        subject = f"You've been invited to join workspace: {getattr(instance.workspace, 'name', '')}"
        message = (
            f"Hello,\n\n"
            f"You have been invited to join the workspace '{getattr(instance.workspace, 'name', '')}' "
            f"on {settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'our platform'}.\n\n"
            f"Invitation ID: {instance.pk}\n"
            f"To accept the invitation please follow the link provided in the app or use the invitation code.\n\n"
            "If you did not expect this invitation, please ignore this email.\n"
        )
        recipient = instance.email
        # Use Django send_mail; ensure EMAIL_* settings are configured in production
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        # Don't let email failure interrupt workspace creation; log for troubleshooting.
        logger.exception("Failed to send workspace invitation email to %s", getattr(instance, "email", None))
