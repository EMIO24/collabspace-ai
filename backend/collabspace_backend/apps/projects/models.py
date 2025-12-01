"""
Project models for CollabSpace AI.

Handles project management, project members, and project labels.
"""

import uuid
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.core.models import BaseModel, TimeStampedModel


class Project(BaseModel):
    """
    Project model representing a project within a workspace.
    
    Projects contain tasks and are managed by workspace members.
    """
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='projects'
    )
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, db_index=True)
    description = models.TextField(blank=True)
    
    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    
    # Status & Priority
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('archived', 'Archived'),
            ('completed', 'Completed'),
            ('on_hold', 'On Hold'),
        ],
        default='active',
        db_index=True
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium',
        db_index=True
    )
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Customization
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text='Hex color code for project'
    )
    icon = models.CharField(max_length=50, blank=True, help_text='Icon name or emoji')
    
    # Visibility
    is_public = models.BooleanField(
        default=False,
        help_text='If True, project is visible to all workspace members'
    )
    
    # Settings
    settings = models.JSONField(
        default=dict,
        help_text='Project configuration settings'
    )
    
    # Cached Counts (for performance)
    task_count = models.IntegerField(default=0)
    completed_task_count = models.IntegerField(default=0)
    member_count = models.IntegerField(default=1)
    
    # Progress
    progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='Project completion percentage'
    )
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        unique_together = ['workspace', 'slug']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['workspace', 'owner']),
            models.Index(fields=['owner']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['slug']),
        ]
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f'{self.workspace.name} - {self.name}'
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate slug and set default settings."""
        if not self.slug:
            self.slug = self._generate_unique_slug()
        
        # Set default settings if not provided
        if not self.settings:
            self.settings = {
                'enable_time_tracking': True,
                'enable_subtasks': True,
                'enable_comments': True,
                'enable_attachments': True,
                'auto_archive_completed_tasks': False,
                'require_task_approval': False,
                'default_task_view': 'list',
            }
        
        super().save(*args, **kwargs)
    
    def _generate_unique_slug(self):
        """Generate a unique slug within the workspace."""
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        while Project.objects.filter(workspace=self.workspace, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        
        # Validate dates
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError('End date must be after start date')
        
        # Validate color
        if self.color and not self.color.startswith('#'):
            raise ValidationError('Color must be a valid hex code starting with #')
    
    # ------------------------------
    # Member Management Methods
    # ------------------------------
    
    def add_member(self, user, role='member', added_by=None):
        """
        Add a member to the project.
        
        Args:
            user: User instance to add
            role: Member role (owner/admin/member)
            added_by: User who added this member
        
        Returns:
            ProjectMember instance
        
        Raises:
            ValidationError: If user not in workspace
        """
        # Check workspace membership
        if not self.workspace.is_member(user):
            raise ValidationError(f'{user.email} is not a member of the workspace')
        
        # Create or update member
        member, created = ProjectMember.objects.get_or_create(
            project=self,
            user=user,
            defaults={'role': role, 'added_by': added_by}
        )
        
        if not created and member.role != role:
            member.role = role
            member.save(update_fields=['role'])
        
        # Update member count
        self.update_counts()
        return member
    
    def remove_member(self, user):
        """
        Remove a member from the project.
        """
        if self.is_owner(user):
            raise ValidationError('Cannot remove project owner')
        
        member = ProjectMember.objects.filter(project=self, user=user).first()
        if not member:
            raise ValidationError(f'{user.email} is not a member of this project')
        
        member.delete()
        self.update_counts()
    
    def update_member_role(self, user, new_role):
        """
        Update a member's role in the project.
        """
        if self.is_owner(user):
            raise ValidationError('Cannot change owner role')
        
        member = ProjectMember.objects.filter(project=self, user=user).first()
        if not member:
            raise ValidationError(f'{user.email} is not a member of this project')
        
        member.role = new_role
        member.save(update_fields=['role'])
    
    def is_member(self, user):
        """Check if user is a member of this project."""
        return ProjectMember.objects.filter(project=self, user=user).exists()
    
    def is_owner(self, user):
        """Check if user is the owner of this project."""
        return self.owner == user
    
    def is_admin(self, user):
        """Check if user is an admin of this project."""
        if self.is_owner(user):
            return True
        
        member = ProjectMember.objects.filter(project=self, user=user).first()
        return member.role in ['admin', 'owner'] if member else False
    
    def get_member_role(self, user):
        """Get the role of a user in this project."""
        member = ProjectMember.objects.filter(project=self, user=user).first()
        return member.role if member else None
    
    # ------------------------------
    # Progress & Statistics
    # ------------------------------
    
    def calculate_progress(self):
        """Calculate project completion progress."""
        if self.task_count == 0:
            return 0.00
        return round((self.completed_task_count / self.task_count) * 100, 2)
    
    def update_counts(self):
        """Update cached task and member counts."""
        self.member_count = ProjectMember.objects.filter(project=self).count()
        # Task counts will be updated when tasks module is added
        
        self.progress = self.calculate_progress()
        self.save(update_fields=['member_count', 'task_count', 'completed_task_count', 'progress'])
    
    def get_statistics(self):
        """Get comprehensive project statistics."""
        return {
            'total_tasks': self.task_count,
            'completed_tasks': self.completed_task_count,
            'pending_tasks': self.task_count - self.completed_task_count,
            'progress_percentage': float(self.progress),
            'total_members': self.member_count,
            'status': self.status,
            'priority': self.priority,
            'days_active': (timezone.now().date() - self.created_at.date()).days,
            'is_overdue': self.is_overdue(),
        }
    
    def is_overdue(self):
        """Check if project is overdue."""
        if not self.end_date:
            return False
        return timezone.now().date() > self.end_date and self.status != 'completed'
    
    def archive(self):
        """Archive the project."""
        self.status = 'archived'
        self.save(update_fields=['status'])
    
    def restore(self):
        """Restore archived project."""
        if self.status == 'archived':
            self.status = 'active'
            self.save(update_fields=['status'])
    
    def complete(self):
        """Mark project as completed."""
        self.status = 'completed'
        self.save(update_fields=['status'])
    
    @property
    def completion_percentage(self):
        return float(self.progress)
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_archived(self):
        return self.status == 'archived'
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def duration_days(self):
        if not self.start_date or not self.end_date:
            return None
        return (self.end_date - self.start_date).days


class ProjectMember(TimeStampedModel):
    """
    Project membership model.
    
    Represents the relationship between a user and a project.
    """
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    
    role = models.CharField(
        max_length=20,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
        ],
        default='member',
        db_index=True
    )
    
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_project_members'
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_members'
        unique_together = ['project', 'user']
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['project', 'user']),
            models.Index(fields=['project', 'role']),
            models.Index(fields=['user']),
        ]
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'
    
    def __str__(self):
        return f'{self.user.email} - {self.project.name} ({self.role})'
    
    def can_manage_project(self):
        return self.role in ['owner', 'admin']
    
    def can_add_members(self):
        return self.role in ['owner', 'admin']
    
    def can_create_tasks(self):
        return True
    
    def can_delete_tasks(self):
        return self.role in ['owner', 'admin']


class ProjectLabel(TimeStampedModel):
    """
    Project label model for categorizing tasks.
    
    Labels can be used to tag and filter tasks within a project.
    """
    
    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='labels'
    )
    
    # Label Information
    name = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7,
        default='#6B7280',
        help_text='Hex color code for label'
    )
    description = models.TextField(blank=True)
    
    # Creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_project_labels'
    )
    
    class Meta:
        db_table = 'project_labels'
        ordering = ['name']
        unique_together = ['project', 'name']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['name']),
        ]
        verbose_name = 'Project Label'
        verbose_name_plural = 'Project Labels'
    
    def __str__(self):
        return f'{self.project.name} - {self.name}'
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        
        # Validate color format
        if self.color and not self.color.startswith('#'):
            raise ValidationError('Color must be a valid hex code starting with #')
        
        # Validate name length
        if len(self.name) < 2:
            raise ValidationError('Label name must be at least 2 characters')
    
    @property
    def task_count(self):
        """Get number of tasks with this label."""
        # This will work when tasks module is added
        # return self.tasks.filter(is_deleted=False).count()
        return 0


class ProjectTemplate(TimeStampedModel):
    """
    Project template model for quick project creation.
    
    Templates allow users to create projects with predefined structure.
    """
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template Owner
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='project_templates',
        null=True,
        blank=True,
        help_text='If set, template is private to workspace'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_project_templates'
    )
    
    # Template Data
    template_data = models.JSONField(
        default=dict,
        help_text='Template configuration including default tasks, labels, etc.'
    )
    
    # Visibility
    is_public = models.BooleanField(
        default=False,
        help_text='If True, template is available to all users'
    )
    
    # Usage Statistics
    use_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'project_templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_public']),
        ]
        verbose_name = 'Project Template'
        verbose_name_plural = 'Project Templates'
    
    def __str__(self):
        return self.name
    
    def increment_use_count(self):
        """Increment the template usage counter."""
        self.use_count += 1
        self.save(update_fields=['use_count'])
    
    def apply_to_project(self, project):
        """
        Apply template to a project.
        
        Args:
            project: Project instance to apply template to
        """
        # Apply template settings
        if 'settings' in self.template_data:
            project.settings.update(self.template_data['settings'])
            project.save(update_fields=['settings'])
        
        # Create labels from template
        if 'labels' in self.template_data:
            for label_data in self.template_data['labels']:
                ProjectLabel.objects.create(
                    project=project,
                    name=label_data['name'],
                    color=label_data.get('color', '#6B7280'),
                    description=label_data.get('description', ''),
                    created_by=project.owner
                )
        
        # Create default tasks from template (when tasks module is added)
        # if 'tasks' in self.template_data:
        #     for task_data in self.template_data['tasks']:
        #         Task.objects.create(
        #             project=project,
        #             title=task_data['title'],
        #             description=task_data.get('description', ''),
        #             created_by=project.owner
        #         )
        
        self.increment_use_count()


class ProjectActivity(TimeStampedModel):
    """
    Project activity log model.
    
    Tracks all activities within a project for audit and timeline.
    """
    
    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='project_activities'
    )
    
    # Activity Details
    action = models.CharField(
        max_length=50,
        choices=[
            ('created', 'Created'),
            ('updated', 'Updated'),
            ('deleted', 'Deleted'),
            ('archived', 'Archived'),
            ('restored', 'Restored'),
            ('member_added', 'Member Added'),
            ('member_removed', 'Member Removed'),
            ('task_created', 'Task Created'),
            ('task_completed', 'Task Completed'),
        ],
        db_index=True
    )
    
    description = models.TextField(help_text='Human-readable activity description')
    
    # Activity Metadata
    metadata = models.JSONField(
        default=dict,
        help_text='Additional activity data'
    )
    
    class Meta:
        db_table = 'project_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
        ]
        verbose_name = 'Project Activity'
        verbose_name_plural = 'Project Activities'
    
    def __str__(self):
        return f'{self.project.name} - {self.action} by {self.user.email if self.user else "System"}'