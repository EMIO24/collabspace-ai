"""
CollabSpace AI - Tasks Module Models (FINAL)
Includes Fixes 1-4 for Metadata JSON Serialization Issues AND UUID String Conversion.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q, F
from django.utils import timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any

# Assuming these are imported from apps.core.models
class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    class Meta:
        abstract = True
        
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

User = get_user_model()


class TaskManager(models.Manager):
    """Custom manager for Task model with common queries."""
    
    def for_user(self, user):
        """Get tasks assigned to or created by user."""
        return self.filter(Q(assigned_to=user) | Q(created_by=user))
    
    def by_status(self, status):
        """Get tasks by status."""
        return self.filter(status=status, is_active=True)
    
    def overdue(self):
        """Get overdue tasks."""
        return self.filter(
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress', 'review'],
            is_active=True
        )
    
    def by_priority(self, priority):
        """Get tasks by priority."""
        return self.filter(priority=priority, is_active=True)
    
    def root_tasks(self):
        """Get only root tasks (no parent)."""
        return self.filter(parent_task__isnull=True, is_active=True)


class Task(BaseModel, TimeStampedModel):
    """
    Core Task model with comprehensive project management features.
    Supports subtasks, dependencies, time tracking, checklist and rich metadata.
    """
    
    # Status choices
    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_REVIEW = 'review'
    STATUS_DONE = 'done'
    
    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_REVIEW, 'Review'),
        (STATUS_DONE, 'Done'),
    ]
    
    # Priority choices
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]
    
    # Core fields
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text='Project this task belongs to'
    )
    
    title = models.CharField(
        max_length=500,
        help_text='Task title/summary'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Rich text description of the task'
    )
    
    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_TODO,
        db_index=True,
        help_text='Current task status'
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        db_index=True,
        help_text='Task priority level'
    )
    
    # Assignment and ownership
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text='User assigned to this task'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        help_text='User who created this task'
    )
    
    # Dates and time tracking
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Task due date and time'
    )

    completed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        db_index=True, 
        help_text="Timestamp when task was marked done"
    )
    
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Estimated hours to complete'
    )
    
    # Tags for categorization
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text='Array of tag strings for categorization'
    )
    
    # Ordering within project/board
    position = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Position for manual ordering'
    )
    
    # Hierarchical structure
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks',
        help_text='Parent task for subtask hierarchy'
    )
    
    # Flexible metadata storage
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional flexible metadata. Used for: checklist'
    )
    
    # Custom manager
    objects = TaskManager()
    
    class Meta:
        ordering = ['position', '-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['parent_task']),
            models.Index(fields=['project', 'completed_at']),
        ]
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def clean(self):
        """Validate task data."""
        super().clean()
        
        # Prevent circular parent relationships
        if self.parent_task:
            if self.parent_task == self:
                raise ValidationError("A task cannot be its own parent.")
            
            parent = self.parent_task
            while parent:
                if parent == self:
                    raise ValidationError("Circular parent relationship detected.")
                parent = parent.parent_task
        
        # Validate estimated hours
        if self.estimated_hours and self.estimated_hours < 0:
            raise ValidationError("Estimated hours cannot be negative.")
        
        # Validate that parent task belongs to same project
        if self.parent_task and self.parent_task.project != self.project:
            raise ValidationError("Parent task must belong to the same project.")
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    # --- HELPER METHOD: Ensure metadata is valid ---
    def _ensure_metadata_dict(self):
        """Ensure metadata is always a valid dictionary."""
        if not isinstance(self.metadata, dict):
            self.metadata = {}
    
    # --- CHECKLIST METHODS ---
    
    def get_checklist_items(self) -> List[Dict[str, Any]]:
        """Get the list of checklist items from metadata."""
        self._ensure_metadata_dict()
        return self.metadata.get('checklist', [])

    def add_checklist_item(self, text: str, is_completed: bool = False):
        """Add a new checklist item and save."""
        self._ensure_metadata_dict()
        
        # Create a new dict to force Django to recognize the change
        metadata_copy = dict(self.metadata)
        checklist = metadata_copy.get('checklist', [])
        
        checklist.append({
            'id': len(checklist) + 1,
            'text': text,
            'is_completed': is_completed,
            'created_at': timezone.now().isoformat(),
        })
        
        metadata_copy['checklist'] = checklist
        self.metadata = metadata_copy
        
        self.save(update_fields=['metadata'])

    def get_checklist_progress(self) -> float:
        """Calculate checklist completion percentage."""
        checklist = self.get_checklist_items()
        total = len(checklist)
        if total == 0:
            return 0.0
        completed = sum(1 for item in checklist if item.get('is_completed'))
        return (completed / total) * 100

    # Time tracking methods
    def get_actual_hours(self) -> Decimal:
        """Calculate actual hours logged from time entries."""
        total = self.time_entries.aggregate(
            total=Sum('hours')
        )['total']
        return total or Decimal('0.00')
    
    @property
    def actual_hours(self) -> Decimal:
        """Property for actual hours worked."""
        return self.get_actual_hours()
    
    def get_time_remaining(self) -> Optional[Decimal]:
        """Calculate remaining hours based on estimate and actual."""
        if not self.estimated_hours:
            return None
        return max(Decimal('0.00'), self.estimated_hours - self.actual_hours)
    
    def get_time_progress_percentage(self) -> Optional[float]:
        """Calculate time progress percentage."""
        if not self.estimated_hours or self.estimated_hours == 0:
            return None
        percentage = (float(self.actual_hours) / float(self.estimated_hours)) * 100
        return min(percentage, 100.0)
    
    # Subtask methods
    def get_all_subtasks(self, include_self: bool = False) -> List['Task']:
        """Get all subtasks recursively."""
        subtasks = []
        if include_self:
            subtasks.append(self)
        
        for subtask in self.subtasks.filter(is_active=True):
            subtasks.append(subtask)
            subtasks.extend(subtask.get_all_subtasks(include_self=False))
        
        return subtasks
    
    def get_subtask_count(self) -> int:
        """Get total count of all subtasks recursively."""
        return len(self.get_all_subtasks())
    
    def get_completed_subtasks_count(self) -> int:
        """Get count of completed subtasks."""
        all_subtasks = self.get_all_subtasks()
        return sum(1 for task in all_subtasks if task.status == self.STATUS_DONE)
    
    def get_subtask_progress_percentage(self) -> float:
        """Calculate subtask completion percentage."""
        total = self.get_subtask_count()
        if total == 0:
            return 0.0
        completed = self.get_completed_subtasks_count()
        return (completed / total) * 100
    
    def is_root_task(self) -> bool:
        """Check if this is a root task (no parent)."""
        return self.parent_task is None
    
    def get_depth_level(self) -> int:
        """Get the depth level in the task hierarchy."""
        level = 0
        parent = self.parent_task
        while parent:
            level += 1
            parent = parent.parent_task
        return level
    
    def get_root_task(self) -> 'Task':
        """Get the root task in the hierarchy."""
        if self.is_root_task():
            return self
        parent = self.parent_task
        while parent.parent_task:
            parent = parent.parent_task
        return parent
    
    # Dependency methods
    def add_dependency(self, depends_on_task: 'Task', 
                        dependency_type: str = 'blocks') -> 'TaskDependency':
        """Add a dependency to another task."""
        return TaskDependency.objects.create(
            task=self,
            depends_on=depends_on_task,
            dependency_type=dependency_type
        )
    
    def get_blocking_tasks(self) -> List['Task']:
        """Get tasks that are blocking this task."""
        dependency_ids = self.dependencies.filter(
            dependency_type=TaskDependency.TYPE_BLOCKS
        ).values_list('depends_on_id', flat=True)
        return Task.objects.filter(id__in=dependency_ids, is_active=True)
    
    def get_blocked_tasks(self) -> List['Task']:
        """Get tasks that this task is blocking."""
        dependency_ids = TaskDependency.objects.filter(
            depends_on=self,
            dependency_type=TaskDependency.TYPE_BLOCKS
        ).values_list('task_id', flat=True)
        return Task.objects.filter(id__in=dependency_ids, is_active=True)
    
    def is_blocked(self) -> bool:
        """Check if task is blocked by incomplete dependencies."""
        blocking_tasks = self.get_blocking_tasks()
        return any(task.status != self.STATUS_DONE for task in blocking_tasks)
    
    def can_start(self) -> bool:
        """Check if task can be started (no incomplete blocking dependencies)."""
        return not self.is_blocked()
    
    # --- HELPER FOR AI ANALYTICS ---
    def _record_status_change(self, old_status, new_status, user):
        """Helper to create history records for AI bottleneck analysis."""
        if old_status == new_status:
            return

        last_history = self.status_history.order_by('-created_at').first()
        duration = 0
        if last_history:
            diff = timezone.now() - last_history.created_at
            duration = diff.total_seconds() / 3600.0

        TaskStatusHistory.objects.create(
            task=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            duration_hours=Decimal(duration) if last_history else None
        )

    # --- UPDATED ASSIGNMENT & STATUS METHODS WITH METADATA VALIDATION ---

    def assign(self, user: User, assigned_by: User = None):
        """
        Assign task to a user and record audit metadata.
        FIXED: Ensures metadata is always a valid dict before saving.
        FIXED: Converts UUID to string for JSON serialization.
        """
        if self.assigned_to == user:
            return

        self.assigned_to = user
        
        # ✅ ROBUST FIX: Ensure metadata is always a valid dictionary
        self._ensure_metadata_dict()
        
        # Record assignment history in metadata
        if assigned_by:
            # Create a new dict to force Django to recognize the change
            metadata_copy = dict(self.metadata)
            # ✅ Convert UUID to string
            metadata_copy['assigned_by'] = str(assigned_by.id)
            metadata_copy['assigned_at'] = timezone.now().isoformat()
            self.metadata = metadata_copy
            
        self.save(update_fields=['assigned_to', 'metadata', 'updated_at'])

    def mark_as_done(self, user: User = None):
        """
        Mark task as done, update metadata, and record history for Analytics.
        FIXED: Ensures metadata is always a valid dict before saving.
        FIXED: Converts UUID to string for JSON serialization.
        """
        # Record history before changing status
        self._record_status_change(self.status, self.STATUS_DONE, user)
        
        self.status = self.STATUS_DONE
        self.completed_at = timezone.now()
        
        # ✅ ROBUST FIX: Ensure metadata is always a valid dictionary
        self._ensure_metadata_dict()
        
        # Create a new dict to force Django to recognize the change
        metadata_copy = dict(self.metadata)
        if user:
             # ✅ Convert UUID to string
            metadata_copy['completed_by'] = str(user.id)
        metadata_copy['completed_at'] = timezone.now().isoformat()
        self.metadata = metadata_copy
        
        self.save()
    
    def mark_as_in_progress(self, user: User = None):
        """
        Mark task as in progress and record history for Analytics.
        FIXED: Ensures metadata is always a valid dict before saving.
        FIXED: Converts UUID to string for JSON serialization.
        """
        if not self.can_start():
            raise ValidationError("Cannot start task: blocked by dependencies.")
        
        # Record history before changing status
        self._record_status_change(self.status, self.STATUS_IN_PROGRESS, user)
        
        self.status = self.STATUS_IN_PROGRESS
        
        # ✅ ROBUST FIX: Ensure metadata is always a valid dictionary
        self._ensure_metadata_dict()
        
        if user and not self.metadata.get('started_by'):
            # Create a new dict to force Django to recognize the change
            metadata_copy = dict(self.metadata)
             # ✅ Convert UUID to string
            metadata_copy['started_by'] = str(user.id)
            metadata_copy['started_at'] = timezone.now().isoformat()
            self.metadata = metadata_copy
        
        self.save()
    
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return (
            self.due_date < timezone.now() and 
            self.status not in [self.STATUS_DONE]
        )
    
    # Collaboration methods
    def get_collaborators(self) -> List[User]:
        """Get all users involved with this task."""
        user_ids = set()
        
        if self.assigned_to:
            user_ids.add(self.assigned_to.id)
        
        if self.created_by:
            user_ids.add(self.created_by.id)
        
        comment_users = self.comments.values_list('user_id', flat=True)
        user_ids.update(comment_users)
        
        time_entry_users = self.time_entries.values_list('user_id', flat=True)
        user_ids.update(time_entry_users)
        
        return User.objects.filter(id__in=user_ids)
    
    def get_activity_count(self) -> Dict[str, int]:
        """Get counts of various activities on this task."""
        return {
            'comments': self.comments.count(),
            'attachments': self.attachments.count(),
            'time_entries': self.time_entries.count(),
            'subtasks': self.subtasks.count(),
            'dependencies': self.dependencies.count(),
            'checklist_items': len(self.get_checklist_items()),
        }
    
    def matches_tags(self, tags: List[str]) -> bool:
        """Check if task has any of the given tags."""
        return any(tag in self.tags for tag in tags)
    
    def get_similar_tasks(self, limit: int = 5) -> List['Task']:
        """Get similar tasks based on tags and project."""
        if not self.tags:
            return []
        
        return Task.objects.filter(
            project=self.project,
            is_active=True
        ).exclude(
            id=self.id
        ).filter(
            tags__overlap=self.tags
        )[:limit]


# ============================================================================
# TaskStatusHistory Model
# ============================================================================

class TaskStatusHistory(models.Model):
    """Tracks the history of status changes for bottleneck analysis."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'new_status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Task Status History'
        verbose_name_plural = 'Task Status Histories'


class TaskDependency(models.Model):
    """Model for task dependencies to manage task relationships."""
    
    TYPE_BLOCKS = 'blocks'
    TYPE_BLOCKED_BY = 'blocked_by'
    
    DEPENDENCY_TYPE_CHOICES = [
        (TYPE_BLOCKS, 'Blocks'),
        (TYPE_BLOCKED_BY, 'Blocked By'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependencies',
        help_text='The dependent task'
    )
    
    depends_on = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependents',
        help_text='The task this depends on'
    )
    
    dependency_type = models.CharField(
        max_length=20,
        choices=DEPENDENCY_TYPE_CHOICES,
        default=TYPE_BLOCKS,
        help_text='Type of dependency relationship'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['task', 'depends_on', 'dependency_type']
        verbose_name = 'Task Dependency'
        verbose_name_plural = 'Task Dependencies'
        indexes = [
            models.Index(fields=['task', 'dependency_type']),
        ]
    
    def __str__(self):
        return f"{self.task.title} {self.dependency_type} {self.depends_on.title}"
    
    def clean(self):
        """Validate dependency doesn't create cycles."""
        if self.task == self.depends_on:
            raise ValidationError("A task cannot depend on itself.")
        
        if self._creates_circular_dependency():
            raise ValidationError("This dependency would create a circular relationship.")
        
        if self.task.project != self.depends_on.project:
            raise ValidationError("Dependencies must be within the same project.")
    
    def _creates_circular_dependency(self) -> bool:
        """Check if this dependency would create a circular relationship."""
        visited = set()
        stack = [self.depends_on]
        
        while stack:
            current = stack.pop()
            if current.id == self.task.id:
                return True
            
            if current.id in visited:
                continue
            
            visited.add(current.id)
            
            for dep in current.dependencies.filter(dependency_type=self.TYPE_BLOCKS):
                stack.append(dep.depends_on)
        
        return False
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)


class TaskComment(BaseModel, TimeStampedModel):
    """Task comments with threading support."""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Task this comment belongs to'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_comments',
        help_text='User who wrote this comment'
    )
    
    content = models.TextField(
        help_text='Comment content (supports markdown)'
    )
    
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text='Parent comment for threaded replies'
    )
    
    mentions = models.ManyToManyField(
        User,
        related_name='mentioned_in_task_comments',
        blank=True,
        help_text='Users mentioned in this comment'
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['user']),
            models.Index(fields=['parent_comment']),
        ]
        verbose_name = 'Task Comment'
        verbose_name_plural = 'Task Comments'
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"
    
    def clean(self):
        """Validate comment data."""
        super().clean()
        
        if self.parent_comment:
            depth = self.get_thread_depth()
            if depth > 5:
                raise ValidationError("Comment threading is limited to 5 levels.")
    
    def get_thread_depth(self) -> int:
        """Get the depth of this comment in the thread."""
        depth = 0
        parent = self.parent_comment
        while parent:
            depth += 1
            parent = parent.parent_comment
        return depth
    
    def get_reply_count(self) -> int:
        """Get the count of direct replies."""
        return self.replies.filter(is_active=True).count()
    
    def get_all_replies(self) -> List['TaskComment']:
        """Get all replies recursively."""
        replies = []
        for reply in self.replies.filter(is_active=True):
            replies.append(reply)
            replies.extend(reply.get_all_replies())
        return replies
    
    def is_edited(self) -> bool:
        """Check if comment has been edited."""
        return self.updated_at > self.created_at
    
    def extract_mentions(self) -> List[str]:
        """Extract @mentions from content."""
        import re
        pattern = r'@(\w+)'
        return re.findall(pattern, self.content)
    
    def notify_mentions(self):
        """Notify mentioned users."""
        mentioned_usernames = self.extract_mentions()
        mentioned_users = User.objects.filter(username__in=mentioned_usernames)
        self.mentions.set(mentioned_users)


class TaskAttachment(TimeStampedModel):
    """File attachments for tasks."""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text='Task this attachment belongs to'
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_attachments',
        help_text='User who uploaded this file'
    )
    
    file_name = models.CharField(
        max_length=255,
        help_text='Original file name'
    )
    
    file_url = models.URLField(
        max_length=500,
        help_text='URL to the stored file'
    )
    
    file_size = models.BigIntegerField(
        help_text='File size in bytes'
    )
    
    file_type = models.CharField(
        max_length=100,
        help_text='MIME type of the file'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['uploaded_by']),
        ]
        verbose_name = 'Task Attachment'
        verbose_name_plural = 'Task Attachments'
    
    def __str__(self):
        return f"{self.file_name} on {self.task.title}"
    
    def get_file_size_display(self) -> str:
        """Get human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        return self.file_type.startswith('image/')
    
    def is_document(self) -> bool:
        """Check if attachment is a document."""
        doc_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument',
            'text/plain',
        ]
        return any(self.file_type.startswith(doc_type) for doc_type in doc_types)


class TimeEntry(TimeStampedModel):
    """Time tracking entries for tasks."""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text='Task this time entry is for'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text='User who logged this time'
    )
    
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text='Hours worked'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Description of work performed'
    )
    
    date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text='Date when work was performed'
    )
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['task', 'date']),
            models.Index(fields=['user', 'date']),
        ]
        verbose_name = 'Time Entry'
        verbose_name_plural = 'Time Entries'
    
    def __str__(self):
        return f"{self.hours}h by {self.user.username} on {self.task.title}"
    
    def clean(self):
        """Validate time entry data."""
        if self.hours <= 0:
            raise ValidationError("Hours must be greater than zero.")
        
        if self.hours > 24:
            raise ValidationError("Cannot log more than 24 hours per entry.")
        
        if self.date > timezone.now().date():
            raise ValidationError("Cannot log time for future dates.")
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @staticmethod
    def get_total_hours_for_user(user: User, start_date=None, end_date=None) -> Decimal:
        """Get total hours logged by user in date range."""
        queryset = TimeEntry.objects.filter(user=user)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        total = queryset.aggregate(total=Sum('hours'))['total']
        return total or Decimal('0.00')
    
    @staticmethod
    def get_total_hours_for_task(task: Task) -> Decimal:
        """Get total hours logged for a task."""
        total = TimeEntry.objects.filter(task=task).aggregate(
            total=Sum('hours')
        )['total']
        return total or Decimal('0.00')


class TaskTemplate(BaseModel, TimeStampedModel):
    """
    Reusable task templates for common task types.
    Users can create templates and instantiate tasks from them.
    """
    
    name = models.CharField(
        max_length=200,
        help_text='Template name'
    )

    description = models.TextField(
        blank=True,
        help_text='Template description'
    )
    
    # Template fields
    title_template = models.CharField(
        max_length=500,
        help_text='Task title template (supports variables like {project_name})'
    )
    
    description_template = models.TextField(
        blank=True,
        help_text='Task description template'
    )
    
    default_priority = models.CharField(
        max_length=20,
        choices=Task.PRIORITY_CHOICES, # Reuse Task priority choices
        default=Task.PRIORITY_MEDIUM
    )
    
    default_estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    default_tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )
    
    # Template configuration
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text='Template category (e.g., Bug Fix, Feature, Research)'
    )
    
    is_public = models.BooleanField(
        default=False,
        help_text='Whether this template is available to all users'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_templates'
    )
    
    # Subtask templates structure: [{'title': '...', 'description': '...', 'priority': '...'}]
    subtask_templates = models.JSONField(
        default=list,
        blank=True,
        help_text='List of subtask templates to create'
    )
    
    # Checklist items structure: [{'text': '...', 'is_completed': False}]
    checklist_items = models.JSONField(
        default=list,
        blank=True,
        help_text='Default checklist items'
    )
    
    usage_count = models.IntegerField(
        default=0,
        help_text='Number of times this template has been used'
    )
    
    class Meta:
        ordering = ['-usage_count', 'name']
        verbose_name = 'Task Template'
        verbose_name_plural = 'Task Templates'
        indexes = [
            models.Index(fields=['category', 'is_public']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return self.name
    
    def create_task_from_template(self, project, assigned_to=None, created_by=None, **kwargs):
        """
        Create a task instance from this template.
        """
        
        # Interpolate template variables
        context = {
            'project_name': project.name,
            **kwargs.get('template_vars', {})
        }
        
        title = self.title_template.format(**context)
        description = self.description_template.format(**context)
        
        # Initialize checklist for the main task
        initial_checklist = [
            {
                'id': i + 1,
                'text': item.get('text'),
                'is_completed': item.get('is_completed', False),
                # Note: Adding current timestamp on creation, not template's
                'created_at': timezone.now().isoformat(),
            }
            for i, item in enumerate(self.checklist_items)
        ]

        # Create main task
        task = Task.objects.create(
            project=project,
            title=kwargs.get('title', title),
            description=kwargs.get('description', description),
            priority=kwargs.get('priority', self.default_priority),
            estimated_hours=kwargs.get('estimated_hours', self.default_estimated_hours),
            tags=kwargs.get('tags', self.default_tags.copy()),
            assigned_to=assigned_to,
            created_by=created_by,
            due_date=kwargs.get('due_date'),
            metadata={'template_id': self.id, 'checklist': initial_checklist}
        )
        
        # Create subtasks if specified
        for subtask_template in self.subtask_templates:
            Task.objects.create(
                project=project,
                title=subtask_template.get('title', '').format(**context),
                description=subtask_template.get('description', '').format(**context),
                priority=subtask_template.get('priority', 'medium'),
                estimated_hours=subtask_template.get('estimated_hours'),
                parent_task=task,
                created_by=created_by,
                metadata={'template_parent_id': self.id}
            )
        
        # Increment usage count
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
        
        return task