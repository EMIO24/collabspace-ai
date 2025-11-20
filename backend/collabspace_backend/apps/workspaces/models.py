import uuid
import secrets
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import timedelta

from apps.core.models import BaseModel, TimeStampedModel


class Workspace(BaseModel):
    """
    Workspace model representing a team workspace.
    
    A workspace is the top-level organization unit where teams collaborate.
    It contains projects, members, and settings.
    """
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    
    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_workspaces'
    )
    
    # Branding
    logo = models.URLField(max_length=500, blank=True)
    
    # Visibility
    is_public = models.BooleanField(
        default=False,
        help_text='If True, workspace is visible to everyone'
    )
    
    # Settings
    settings = models.JSONField(
        default=dict,
        help_text='Workspace configuration settings'
    )
    
    # Plan & Limits
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('pro', 'Pro'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    
    # Cached Counts (for performance)
    member_count = models.IntegerField(default=1)
    project_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'workspaces'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['owner']),
            models.Index(fields=['plan_type']),
            models.Index(fields=['is_public']),
        ]
        verbose_name = 'Workspace'
        verbose_name_plural = 'Workspaces'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate slug and set default settings."""
        if not self.slug:
            self.slug = self._generate_unique_slug()
        
        # Set default settings if not provided
        if not self.settings:
            self.settings = {
                'allow_public_projects': False,
                'require_approval': True,
                'default_project_visibility': 'private',
            }
        
        super().save(*args, **kwargs)
    
    def _generate_unique_slug(self):
        """Generate a unique slug from the workspace name."""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    # Member Management Methods
    
    def add_member(self, user, role='member', invited_by=None):
        """
        Add a member to the workspace.
        
        Args:
            user: User instance to add
            role: Member role (owner/admin/member/guest)
            invited_by: User who invited this member
            
        Returns:
            WorkspaceMember instance
            
        Raises:
            ValidationError: If member limit reached or user already member
        """
        # Check if user is already an active member
        if self.is_member(user):
            raise ValidationError(f'{user.email} is already an active member of this workspace')
        
        # Check plan limits
        if not self.can_add_member():
            raise ValidationError('Member limit reached for your plan')
        
        # Create membership
        member = WorkspaceMember.objects.create(
            workspace=self,
            user=user,
            role=role,
            invited_by=invited_by
        )
        
        # Update member count
        self.update_counts()
        
        return member
    
    def remove_member(self, user):
        """
        Remove a member from the workspace by setting is_active=False.
        
        Args:
            user: User instance to remove
            
        Raises:
            ValidationError: If user is the owner or not an active member
        """
        if self.is_owner(user):
            raise ValidationError('Cannot remove workspace owner')
        
        # Filter for active member
        member = WorkspaceMember.objects.filter(workspace=self, user=user, is_active=True).first()
        if not member:
            raise ValidationError(f'{user.email} is not an active member of this workspace')
        
        # Soft-delete the membership by setting is_active=False
        member.is_active = False
        member.save(update_fields=['is_active'])
        
        self.update_counts()
    
    def update_member_role(self, user, new_role):
        """
        Update a member's role in the workspace.
        
        Args:
            user: User instance
            new_role: New role (admin/member/guest)
            
        Raises:
            ValidationError: If trying to change owner role or user not an active member
        """
        if self.is_owner(user):
            raise ValidationError('Cannot change owner role')
        
        # Filter for active member
        member = WorkspaceMember.objects.filter(workspace=self, user=user, is_active=True).first()
        if not member:
            raise ValidationError(f'{user.email} is not an active member of this workspace')
        
        member.role = new_role
        member.save(update_fields=['role'])
    
    def can_add_member(self):
        """
        Check if workspace can add more members based on plan limits.
        
        Returns:
            bool: True if can add member, False otherwise
        """
        limits = {
            'free': 5,
            'pro': 50,
            'enterprise': -1,  # Unlimited
        }
        
        limit = limits.get(self.plan_type, 5)
        
        if limit == -1:  # Unlimited
            return True
        
        return self.member_count < limit
    
    def get_member_role(self, user):
        """
        Get the role of a user in this workspace.
        
        Args:
            user: User instance
            
        Returns:
            str: Role name or None if not an active member
        """
        member = WorkspaceMember.objects.filter(workspace=self, user=user, is_active=True).first()
        return member.role if member else None
    
    def is_member(self, user):
        """
        Check if user is an active member of this workspace.
        
        Args:
            user: User instance
            
        Returns:
            bool: True if user is an active member
        """
        return WorkspaceMember.objects.filter(workspace=self, user=user, is_active=True).exists()
    
    def is_owner(self, user):
        """
        Check if user is the owner of this workspace.
        
        Args:
            user: User instance
            
        Returns:
            bool: True if user is the owner
        """
        return self.owner == user
    
    def is_admin(self, user):
        """
        Check if user is an admin of this workspace.
        
        Args:
            user: User instance
            
        Returns:
            bool: True if user is owner or admin
        """
        if self.is_owner(user):
            return True
        
        # Filter for active member
        member = WorkspaceMember.objects.filter(workspace=self, user=user, is_active=True).first()
        return member.role in ['admin', 'owner'] if member else False
    
    def update_counts(self):
        """Update cached member and project counts (only counts active members)."""
        self.member_count = WorkspaceMember.objects.filter(workspace=self, is_active=True).count()
        # Project count will be updated when projects module is added
        # from apps.projects.models import Project
        # self.project_count = Project.objects.filter(workspace=self, is_deleted=False).count()
        self.save(update_fields=['member_count', 'project_count'])
    
    @property
    def total_members(self):
        """Get total number of members (property alias)."""
        return self.member_count
    
    @property
    def total_projects(self):
        """Get total number of projects (property alias)."""
        return self.project_count


class WorkspaceMember(TimeStampedModel):
    """
    Workspace membership model.
    
    Represents the relationship between a user and a workspace,
    including their role and permissions.
    """
    
    # Relationships
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships'
    )
    
    # Role & Permissions
    role = models.CharField(
        max_length=20,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
            ('guest', 'Guest'),
        ],
        default='member',
        db_index=True
    )
    
    permissions = models.JSONField(
        default=dict,
        help_text='Custom permissions for this member'
    )
    
    # Invitation tracking
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workspace_invitations_sent'
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # Status - ADDED is_active field
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Designates whether the membership is currently active (used for soft deletion).'
    )
    
    class Meta:
        db_table = 'workspace_members'
        unique_together = ['workspace', 'user']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['workspace', 'user']),
            models.Index(fields=['workspace', 'role']),
            models.Index(fields=['user']),
            models.Index(fields=['is_active']), # Added index for is_active
        ]
        verbose_name = 'Workspace Member'
        verbose_name_plural = 'Workspace Members'
    
    def __str__(self):
        return f'{self.user.email} - {self.workspace.name} ({self.role})'
    
    def save(self, *args, **kwargs):
        """Override save to set default permissions based on role."""
        if not self.permissions:
            self.permissions = self._get_default_permissions()
        
        super().save(*args, **kwargs)
    
    def _get_default_permissions(self):
        """Get default permissions based on role."""
        role_permissions = {
            'owner': {
                'manage_workspace': True,
                'manage_members': True,
                'manage_projects': True,
                'manage_billing': True,
                'delete_workspace': True,
                'invite_members': True,
            },
            'admin': {
                'manage_workspace': False,
                'manage_members': True,
                'manage_projects': True,
                'manage_billing': False,
                'delete_workspace': False,
                'invite_members': True,
            },
            'member': {
                'manage_workspace': False,
                'manage_members': False,
                'manage_projects': False,
                'manage_billing': False,
                'delete_workspace': False,
                'invite_members': False,
            },
            'guest': {
                'manage_workspace': False,
                'manage_members': False,
                'manage_projects': False,
                'manage_billing': False,
                'delete_workspace': False,
                'invite_members': False,
            },
        }
        
        return role_permissions.get(self.role, role_permissions['member'])
    
    def has_permission(self, permission_name):
        """
        Check if member has a specific permission.
        
        Args:
            permission_name: Name of the permission to check
            
        Returns:
            bool: True if member has the permission
        """
        return self.permissions.get(permission_name, False)
    
    def can_invite_members(self):
        """
        Check if member can invite new members.
        
        Returns:
            bool: True if member can invite
        """
        return self.role in ['owner', 'admin'] or self.has_permission('invite_members')
    
    def can_manage_projects(self):
        """
        Check if member can manage projects.
        
        Returns:
            bool: True if member can manage projects
        """
        return self.role in ['owner', 'admin'] or self.has_permission('manage_projects')


class WorkspaceInvitation(TimeStampedModel):
    """
    Workspace invitation model.
    
    Represents an invitation for a user to join a workspace.
    """
    
    # Status Choices for invitation lifecycle - ADDED STATUS FIELD
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_EXPIRED = 'expired'
    STATUS_REVOKED = 'revoked'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_REVOKED, 'Revoked'),
    ]
    
    # Relationships
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    
    # Invitee Information
    email = models.EmailField(db_index=True)
    
    # Invitation Details
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_workspace_invitations'
    )
    
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('member', 'Member'),
            ('guest', 'Guest'),
        ],
        default='member'
    )
    
    # Token & Expiry
    token = models.CharField(max_length=255, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    
    # Status - Replaced is_accepted boolean field with status CharField
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text='Current status of the invitation: pending, accepted, expired, or revoked.'
    )
    
    # is_accepted removed, replaced by status
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_workspace_invitations'
    )
    
    class Meta:
        db_table = 'workspace_invitations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'email']),
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['status']), # Updated index to use status field
        ]
        verbose_name = 'Workspace Invitation'
        verbose_name_plural = 'Workspace Invitations'
    
    def __str__(self):
        return f'Invitation for {self.email} to {self.workspace.name} ({self.get_status_display()})'
    
    def save(self, *args, **kwargs):
        """Override save to generate token, set expiry, and auto-update status to EXPIRED."""
        if not self.token:
            self.token = self._generate_token()
        
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)

        # Auto-set status to EXPIRED if past expiry and still pending
        if self.status == self.STATUS_PENDING and timezone.now() > self.expires_at:
            self.status = self.STATUS_EXPIRED
        
        super().save(*args, **kwargs)
    
    def _generate_token(self):
        """Generate a unique secure token for the invitation."""
        while True:
            token = secrets.token_urlsafe(32)
            if not WorkspaceInvitation.objects.filter(token=token).exists():
                return token
    
    def is_valid(self):
        """
        Check if invitation is still valid.
        
        Returns:
            bool: True if invitation is valid (status is pending and not expired)
        """
        # Only pending invitations can be valid
        if self.status != self.STATUS_PENDING:
            return False
        
        # Check expiry
        if timezone.now() > self.expires_at:
            return False
        
        return True
    
    def send_invitation_email(self):
        """
        Send invitation email to the invitee.
        """
        from apps.authentication.utils import send_email_template
        
        # Construct invitation URL
        invitation_url = f"{settings.FRONTEND_URL}/invitations/accept?token={self.token}"
        
        context = {
            'workspace_name': self.workspace.name,
            'invited_by_name': self.invited_by.get_full_name(),
            'invitation_url': invitation_url,
            'role': self.get_role_display(),
            'expires_at': self.expires_at.strftime('%B %d, %Y'),
        }
        
        # This is a placeholder - implement actual email sending
        # send_email_template(
        #     to_email=self.email,
        #     subject=f'Invitation to join {self.workspace.name}',
        #     template='workspace_invitation.html',
        #     context=context
        # )
        
        print(f"📧 Invitation email would be sent to {self.email}")
        print(f"   URL: {invitation_url}")
    
    def accept(self, user):
        """
        Accept the invitation and add user to workspace.
        
        Args:
            user: User instance accepting the invitation
            
        Raises:
            ValidationError: If invitation is invalid or email doesn't match
        """
        if not self.is_valid():
            # If not valid, the status must be accepted, expired, or revoked
            raise ValidationError('This invitation has expired, been accepted, or revoked.')
        
        if user.email.lower() != self.email.lower():
            raise ValidationError('This invitation is for a different email address')
        
        # Add user to workspace
        self.workspace.add_member(user, role=self.role, invited_by=self.invited_by)
        
        # Mark invitation as accepted
        self.status = self.STATUS_ACCEPTED
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save(update_fields=['status', 'accepted_at', 'accepted_by'])
    
    def cancel(self):
        """Revoke the invitation and update status (for audit trail)."""
        self.status = self.STATUS_REVOKED
        self.save(update_fields=['status'])
    
    @property
    def is_expired(self):
        """Check if invitation has expired."""
        return self.status == self.STATUS_EXPIRED or timezone.now() > self.expires_at
    
    @property
    def is_accepted(self):
        """
        Convenience property to check acceptance status.
        Replaces the old boolean field.
        """
        return self.status == self.STATUS_ACCEPTED

    @property
    def days_until_expiry(self):
        """Get number of days until invitation expires."""
        if self.is_expired:
            return 0
        
        delta = self.expires_at - timezone.now()
        return delta.days