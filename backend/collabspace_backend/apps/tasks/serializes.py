"""
CollabSpace AI - Tasks Module Serializers
Comprehensive serializers for all task-related models with nested relationships,
including extensions for Task Templates, Bulk Operations, and Analytics.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from typing import Dict, Any, List
from decimal import Decimal

# Assuming these models exist in the parent scope for the extension to work
from .models import (
    Task, TaskDependency, TaskComment, TaskAttachment, TimeEntry,
    # New models from the extension (assuming they are in .models too)
    TaskTemplate # Assuming SubtaskTemplate and ChecklistItem are related to TaskTemplate
)

# You might need to adjust the import for Project if it's not defined in the same models file
# from apps.projects.models import Project

User = get_user_model()

# --- Core Serializers ---

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representations."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'avatar']
        read_only_fields = fields

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class TaskAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for task attachments."""

    uploaded_by = UserMinimalSerializer(read_only=True)
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    is_document = serializers.BooleanField(read_only=True)

    class Meta:
        model = TaskAttachment
        fields = [
            'id', 'task', 'uploaded_by', 'file_name', 'file_url',
            'file_size', 'file_size_display', 'file_type',
            'is_image', 'is_document', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create attachment with current user."""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class TimeEntrySerializer(serializers.ModelSerializer):
    """Serializer for time entries."""

    user = UserMinimalSerializer(read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            'id', 'task', 'task_title', 'user', 'hours',
            'description', 'date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_hours(self, value):
        """Validate hours is reasonable."""
        if value <= 0:
            raise serializers.ValidationError("Hours must be greater than zero.")
        if value > 24:
            raise serializers.ValidationError("Cannot log more than 24 hours per entry.")
        return value

    def validate_date(self, value):
        """Validate date is not in the future."""
        if value > timezone.now().date():
            raise serializers.ValidationError("Cannot log time for future dates.")
        return value

    def create(self, validated_data):
        """Create time entry with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments with threading support."""

    user = UserMinimalSerializer(read_only=True)
    mentions = UserMinimalSerializer(many=True, read_only=True)
    mention_usernames = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    reply_count = serializers.IntegerField(source='get_reply_count', read_only=True)
    thread_depth = serializers.IntegerField(source='get_thread_depth', read_only=True)
    is_edited = serializers.BooleanField(read_only=True)
    # Recursively defined field: TaskCommentSerializer will be defined below
    # The 'replies' field needs to be lazily evaluated or defined in a way that avoids circular import.
    # Using SerializerMethodField is the standard way, but we will use the full name for clarity.
    # For simplicity and correctness in a single file:
    replies = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = [
            'id', 'task', 'user', 'content', 'parent_comment',
            'mentions', 'mention_usernames', 'reply_count', 'thread_depth',
            'is_edited', 'replies', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_replies(self, obj):
        """Get direct replies to this comment."""
        # Use a temporary inner class to avoid recursive import errors if TaskCommentSerializer is not yet fully defined
        # or rely on the fact that DRF handles this correctly for SerializerMethodField.
        # Given this is a single file, the latter is usually fine.
        if hasattr(obj, '_prefetched_replies'):
            replies = obj._prefetched_replies
        else:
            # Limit to prevent deep nesting and performance issues
            replies = obj.replies.filter(is_active=True).order_by('created_at')[:5]
        # Recursively call the serializer
        return TaskCommentSerializer(replies, many=True, context=self.context).data

    def create(self, validated_data):
        """Create comment with current user and handle mentions."""
        mention_usernames = validated_data.pop('mention_usernames', [])
        validated_data['user'] = self.context['request'].user

        comment = super().create(validated_data)

        # Handle mentions
        if mention_usernames:
            mentioned_users = User.objects.filter(username__in=mention_usernames)
            comment.mentions.set(mentioned_users)
            # Assuming notify_mentions() is a method on the TaskComment model
            # comment.notify_mentions()

        return comment


class TaskDependencySerializer(serializers.ModelSerializer):
    """Serializer for task dependencies."""

    task_title = serializers.CharField(source='task.title', read_only=True)
    depends_on_title = serializers.CharField(source='depends_on.title', read_only=True)
    depends_on_status = serializers.CharField(source='depends_on.status', read_only=True)

    class Meta:
        model = TaskDependency
        fields = [
            'id', 'task', 'task_title', 'depends_on', 'depends_on_title',
            'depends_on_status', 'dependency_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        """Validate dependency doesn't create cycles and is in the same project."""
        task = attrs.get('task')
        depends_on = attrs.get('depends_on')

        if task == depends_on:
            raise serializers.ValidationError("A task cannot depend on itself.")

        # This check assumes 'task' and 'depends_on' are valid Task instances
        if task and depends_on and task.project != depends_on.project:
            raise serializers.ValidationError(
                "Dependencies must be within the same project."
            )

        # The model is expected to handle the cycle check logic internally or through a clean method.
        # For simplicity in the serializer, we only check for self-dependency and project alignment.
        # The full cycle detection logic (like using a graph traversal) would be too complex for a serializer validate method.

        return attrs


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task lists."""

    assigned_to = UserMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    actual_hours = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    subtask_count = serializers.IntegerField(source='get_subtask_count', read_only=True)
    comment_count = serializers.SerializerMethodField()
    is_blocked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'assigned_to', 'created_by',
            'project', 'project_name', 'due_date', 'estimated_hours',
            'actual_hours', 'tags', 'position', 'parent_task',
            'subtask_count', 'comment_count', 'is_overdue', 'is_blocked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        return obj.comments.filter(is_active=True).count()


class TaskSubtaskSerializer(serializers.ModelSerializer):
    """Nested serializer for subtasks."""

    assigned_to = UserMinimalSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    actual_hours = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'assigned_to',
            'due_date', 'estimated_hours', 'actual_hours',
            'is_overdue', 'position'
        ]
        read_only_fields = fields


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with nested relationships."""

    assigned_to = UserMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    # Nested relationships
    # The `subtasks` field from Task is likely a RelatedManager.
    # The `comments`, `attachments`, `time_entries`, and `dependencies` are also likely RelatedManagers.
    subtasks = TaskSubtaskSerializer(many=True, read_only=True)
    # Comments should be filtered to top-level comments for better presentation
    comments = serializers.SerializerMethodField()
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    time_entries = TimeEntrySerializer(many=True, read_only=True)
    dependencies = TaskDependencySerializer(many=True, read_only=True)

    # Computed fields
    actual_hours = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    time_remaining = serializers.DecimalField(
        max_digits=8, decimal_places=2,
        source='get_time_remaining', read_only=True
    )
    time_progress_percentage = serializers.FloatField(
        source='get_time_progress_percentage', read_only=True
    )
    subtask_count = serializers.IntegerField(source='get_subtask_count', read_only=True)
    completed_subtasks_count = serializers.IntegerField(
        source='get_completed_subtasks_count', read_only=True
    )
    subtask_progress_percentage = serializers.FloatField(
        source='get_subtask_progress_percentage', read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    is_blocked = serializers.BooleanField(read_only=True)
    can_start = serializers.BooleanField(read_only=True)
    blocking_tasks = TaskListSerializer(
        source='get_blocking_tasks', many=True, read_only=True
    )
    blocked_tasks = TaskListSerializer(
        source='get_blocked_tasks', many=True, read_only=True
    )
    collaborators = UserMinimalSerializer(
        source='get_collaborators', many=True, read_only=True
    )
    activity_count = serializers.DictField(
        source='get_activity_count', read_only=True
    )

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'project_name', 'title', 'description',
            'status', 'priority', 'assigned_to', 'created_by',
            'due_date', 'estimated_hours', 'actual_hours',
            'time_remaining', 'time_progress_percentage',
            'tags', 'position', 'parent_task', 'metadata',
            'subtasks', 'subtask_count', 'completed_subtasks_count',
            'subtask_progress_percentage', 'comments', 'attachments',
            'time_entries', 'dependencies', 'blocking_tasks', 'blocked_tasks',
            'is_overdue', 'is_blocked', 'can_start', 'collaborators',
            'activity_count', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_comments(self, obj):
        """Get only top-level, active comments."""
        top_level_comments = obj.comments.filter(
            is_active=True, parent_comment__isnull=True
        ).order_by('created_at')
        # This will recursively include replies via TaskCommentSerializer's get_replies
        return TaskCommentSerializer(
            top_level_comments, many=True, context=self.context
        ).data


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks."""

    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='assigned_to',
        required=False, allow_null=True
    )
    parent_task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(), source='parent_task',
        required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'project', 'title', 'description', 'status', 'priority',
            'assigned_to_id', 'due_date', 'estimated_hours',
            'tags', 'position', 'parent_task_id', 'metadata'
        ]
        extra_kwargs = {
            'project': {'required': True}, # Ensure project is required for creation
            'title': {'required': True},
        }

    # Removed custom validate_assigned_to_id and validate_parent_task_id
    # as PrimaryKeyRelatedField handles existence check.

    def create(self, validated_data):
        """Create task with proper field handling."""
        # PrimaryKeyRelatedField handles the mapping, so we just set created_by
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tasks."""

    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='assigned_to',
        required=False, allow_null=True
    )
    parent_task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(), source='parent_task',
        required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority',
            'assigned_to_id', 'due_date', 'estimated_hours',
            'tags', 'position', 'parent_task_id', 'metadata'
        ]

    # Removed custom validate_assigned_to_id and validate_parent_task_id
    # as PrimaryKeyRelatedField handles existence check.
    # Removed custom update() method as DRF handles the PrimaryKeyRelatedField mapping correctly.


class TaskStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating task status."""

    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)

    def update(self, instance, validated_data):
        """Update task status with proper validation."""
        new_status = validated_data['status']
        user = self.context['request'].user

        # Assuming mark_as_in_progress and mark_as_done are methods on the Task model
        if new_status == Task.STATUS_IN_PROGRESS:
            instance.mark_as_in_progress(user)
        elif new_status == Task.STATUS_DONE:
            instance.mark_as_done(user)
        else:
            instance.status = new_status
            instance.save()

        return instance


class BulkTaskSerializer(serializers.Serializer):
    """Serializer for bulk task operations (deprecated in favor of BulkTaskOperationSerializer)."""
    # Retaining for compatibility, but the new serializer is preferred.

    task_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    # Optional fields for bulk update
    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        required=False
    )
    priority = serializers.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        required=False
    )
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )

    def validate_task_ids(self, value):
        """Validate task IDs exist."""
        if not value:
            raise serializers.ValidationError("At least one task ID is required.")

        # Check if tasks exist
        existing_count = Task.objects.filter(id__in=value).count()
        if existing_count != len(value):
            raise serializers.ValidationError("Some task IDs do not exist.")

        return value

    def validate_assigned_to_id(self, value):
        """Validate assigned user exists."""
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value

    @transaction.atomic
    def update_tasks(self, validated_data):
        """Perform bulk update on tasks."""
        task_ids = validated_data.pop('task_ids')
        tasks = Task.objects.filter(id__in=task_ids)

        # Build update dict
        update_fields = {}
        if 'status' in validated_data:
            update_fields['status'] = validated_data['status']
        if 'priority' in validated_data:
            update_fields['priority'] = validated_data['priority']
        if 'assigned_to_id' in validated_data:
            update_fields['assigned_to_id'] = validated_data['assigned_to_id']
        # Note: tags update needs careful handling for PostgreSQL ArrayField or JSONField
        # Assuming the model handles the list assignment correctly
        if 'tags' in validated_data:
            update_fields['tags'] = validated_data['tags']

        if update_fields:
            tasks.update(**update_fields)

        return tasks

    @transaction.atomic
    def delete_tasks(self, task_ids):
        """Perform bulk soft delete on tasks."""
        Task.objects.filter(id__in=task_ids).update(is_active=False)
        return task_ids


class TaskDuplicateSerializer(serializers.Serializer):
    """Serializer for duplicating tasks."""

    include_subtasks = serializers.BooleanField(default=False)
    include_attachments = serializers.BooleanField(default=False)
    include_comments = serializers.BooleanField(default=False)
    new_title = serializers.CharField(max_length=500, required=False)

    @transaction.atomic
    def duplicate_task(self, task: Task) -> Task:
        """Create a duplicate of the task."""
        user = self.context['request'].user
        include_subtasks = self.validated_data.get('include_subtasks', False)
        include_attachments = self.validated_data.get('include_attachments', False)
        include_comments = self.validated_data.get('include_comments', False)
        new_title = self.validated_data.get('new_title')

        # Create duplicate
        duplicate = Task.objects.create(
            project=task.project,
            title=new_title or f"{task.title} (Copy)",
            description=task.description,
            status=Task.STATUS_TODO,
            priority=task.priority,
            assigned_to=task.assigned_to,
            created_by=user,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            tags=task.tags,
            metadata=task.metadata.copy() if task.metadata else {}
        )

        # Duplicate subtasks if requested
        if include_subtasks:
            self._duplicate_subtasks(task, duplicate, user)

        # Duplicate attachments if requested
        if include_attachments:
            # Assuming TaskAttachment has necessary methods for file handling
            for attachment in task.attachments.all():
                TaskAttachment.objects.create(
                    task=duplicate,
                    uploaded_by=user,
                    file_name=attachment.file_name,
                    # Note: file_url/file copy mechanism is simplified here.
                    # In a real-world scenario, the file itself would need to be copied/cloned
                    # in storage and the new file_url or file field value set.
                    file_url=attachment.file_url,
                    file_size=attachment.file_size,
                    file_type=attachment.file_type
                )

        # Duplicate comments if requested
        if include_comments:
            for comment in task.comments.filter(is_active=True, parent_comment=None):
                self._duplicate_comment(comment, duplicate, user)

        return duplicate

    def _duplicate_subtasks(self, original_task: Task, new_parent: Task, user: User):
        """Recursively duplicate subtasks."""
        for subtask in original_task.subtasks.filter(is_active=True):
            new_subtask = Task.objects.create(
                project=new_parent.project,
                title=subtask.title,
                description=subtask.description,
                status=Task.STATUS_TODO,
                priority=subtask.priority,
                assigned_to=subtask.assigned_to,
                created_by=user,
                due_date=subtask.due_date,
                estimated_hours=subtask.estimated_hours,
                tags=subtask.tags,
                parent_task=new_parent,
                position=subtask.position,
                metadata=subtask.metadata.copy() if subtask.metadata else {}
            )
            # Recursively duplicate nested subtasks
            self._duplicate_subtasks(subtask, new_subtask, user)

    def _duplicate_comment(self, comment: TaskComment, new_task: Task, user: User):
        """Duplicate a comment and its replies."""
        # Duplicating the top-level comment
        new_comment = TaskComment.objects.create(
            task=new_task,
            user=comment.user, # Preserve original user
            content=comment.content
        )
        # Duplicate replies
        for reply in comment.replies.filter(is_active=True):
            TaskComment.objects.create(
                task=new_task,
                user=reply.user, # Preserve original user
                content=reply.content,
                parent_comment=new_comment
            )

# ============================================================================
# SERIALIZERS EXTENSION (Integrated)
# ============================================================================

# Note: TaskTemplate model is assumed to be imported from .models

class TaskTemplateSerializer(serializers.ModelSerializer):
    """Serializer for task templates."""

    # Using UserMinimalSerializer for consistency instead of a dict
    created_by = UserMinimalSerializer(read_only=True)
    can_edit = serializers.SerializerMethodField()
    # Assuming subtask_templates and checklist_items are relationships on the model
    # If they are models, they should use a nested serializer.
    # We will assume they are simple fields or are handled on the model.

    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'name', 'description', 'title_template',
            'description_template', 'default_priority',
            'default_estimated_hours', 'default_tags', 'category',
            'is_public', 'created_by', 'subtask_templates',
            'checklist_items', 'usage_count', 'can_edit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at', 'created_by']
        # Note: 'created_by' is set in create(), not read_only_fields on update

    # The original get_created_by is replaced by the UserMinimalSerializer

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Assuming TaskTemplate model has a created_by field pointing to User
        return obj.created_by == request.user

    def create(self, validated_data):
        if not self.context['request'].user.is_authenticated:
            raise serializers.ValidationError("User must be logged in to create a template.")
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TaskTemplateInstantiateSerializer(serializers.Serializer):
    """Serializer for creating tasks from templates."""

    template_id = serializers.IntegerField(required=True)
    project_id = serializers.IntegerField(required=True)
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)

    # Optional overrides
    title = serializers.CharField(max_length=500, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(
        # Assuming Task.PRIORITY_CHOICES are used
        choices=Task.PRIORITY_CHOICES,
        required=False
    )
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    estimated_hours = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True, min_value=Decimal('0.00')
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    template_vars = serializers.DictField(required=False)

    def validate_template_id(self, value):
        try:
            # TaskTemplate is assumed to be imported
            return TaskTemplate.objects.get(id=value)
        except TaskTemplate.DoesNotExist:
            raise serializers.ValidationError("Template does not exist.")

    def validate_project_id(self, value):
        # Need to import Project model properly
        try:
            # Assuming Project model is available in the environment
            from apps.projects.models import Project
            return Project.objects.get(id=value)
        except ImportError:
            # Fallback if Project model is not accessible
            # This should be fixed in a real project structure
            pass
        except Project.DoesNotExist:
            raise serializers.ValidationError("Project does not exist.")
        return value

    def create_task(self):
        # We need the validated TaskTemplate and Project objects
        template = self.validated_data['template_id']
        project = self.validated_data['project_id']

        assigned_to = None
        if self.validated_data.get('assigned_to_id'):
            # Fetch User object
            try:
                assigned_to = User.objects.get(id=self.validated_data['assigned_to_id'])
            except User.DoesNotExist:
                raise serializers.ValidationError({'assigned_to_id': "User does not exist."})

        # Pop validated object fields that are not part of template.create_task_from_template kwargs
        validated_data_for_task = self.validated_data.copy()
        validated_data_for_task.pop('template_id')
        validated_data_for_task.pop('project_id')

        # Create task from template
        # Assuming template.create_task_from_template exists and handles interpolation
        task = template.create_task_from_template(
            project=project,
            assigned_to=assigned_to,
            created_by=self.context['request'].user,
            **validated_data_for_task
        )

        return task


class TaskReorderSerializer(serializers.Serializer):
    """Serializer for reordering tasks (drag and drop)."""

    task_id = serializers.IntegerField(required=True)
    new_position = serializers.IntegerField(required=True, min_value=0)
    parent_task_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_task_id(self, value):
        try:
            Task.objects.get(id=value, is_active=True)
        except Task.DoesNotExist:
            raise serializers.ValidationError("Task does not exist or is inactive.")
        return value

    def validate_new_position(self, value):
        if value < 0:
            raise serializers.ValidationError("Position must be non-negative.")
        return value


class BulkTaskOperationSerializer(serializers.Serializer):
    """Enhanced bulk operations serializer."""

    task_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1
    )

    operation = serializers.ChoiceField(
        choices=[
            ('update_status', 'Update Status'),
            ('update_priority', 'Update Priority'),
            ('assign', 'Assign User'),
            ('add_tags', 'Add Tags'),
            ('remove_tags', 'Remove Tags'),
            ('set_due_date', 'Set Due Date'),
            ('move_to_project', 'Move to Project'),
            ('archive', 'Archive'),
            ('delete', 'Delete'),
            ('duplicate', 'Duplicate'),
            ('export', 'Export')
        ],
        required=True
    )

    # Operation-specific fields
    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        required=False
    )
    priority = serializers.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        required=False
    )
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    project_id = serializers.IntegerField(required=False)

    def validate_task_ids(self, value):
        existing_count = Task.objects.filter(
            id__in=value, is_active=True
        ).count()
        if existing_count != len(value):
            raise serializers.ValidationError("Some tasks do not exist or are inactive.")
        return value

    # Add general validation for operation-specific fields
    def validate(self, data):
        operation = data.get('operation')
        if operation in ['update_status'] and not data.get('status'):
            raise serializers.ValidationError({'status': "Status is required for 'update_status' operation."})
        if operation in ['update_priority'] and not data.get('priority'):
            raise serializers.ValidationError({'priority': "Priority is required for 'update_priority' operation."})
        if operation in ['assign'] and data.get('assigned_to_id') is None:
             raise serializers.ValidationError({'assigned_to_id': "Assigned user ID is required for 'assign' operation."})
        if operation in ['add_tags', 'remove_tags'] and not data.get('tags'):
            raise serializers.ValidationError({'tags': "Tags are required for tag operations."})
        if operation in ['set_due_date'] and data.get('due_date') is None:
            raise serializers.ValidationError({'due_date': "Due date is required for 'set_due_date' operation."})
        if operation in ['move_to_project'] and not data.get('project_id'):
            raise serializers.ValidationError({'project_id': "Project ID is required for 'move_to_project' operation."})

        # Validate project_id existence
        if data.get('project_id'):
            try:
                from apps.projects.models import Project
                Project.objects.get(id=data['project_id'])
            except ImportError:
                 pass
            except Project.DoesNotExist:
                raise serializers.ValidationError({'project_id': "Project does not exist."})

        # Validate assigned_to_id existence
        if data.get('assigned_to_id') is not None:
            if not User.objects.filter(id=data['assigned_to_id']).exists():
                raise serializers.ValidationError({'assigned_to_id': "User does not exist."})

        return data


class TaskSearchSerializer(serializers.Serializer):
    """Advanced search serializer."""

    query = serializers.CharField(required=True, max_length=500)
    search_fields = serializers.ListField(
        child=serializers.ChoiceField(
            choices=['title', 'description', 'tags', 'comments']
        ),
        required=False,
        default=['title', 'description']
    )
    filters = serializers.DictField(required=False, default=dict)
    limit = serializers.IntegerField(default=50, max_value=200, min_value=1)


class TaskAnalyticsSerializer(serializers.Serializer):
    """Serializer for task analytics queries."""

    project_id = serializers.IntegerField(required=False)
    user_id = serializers.IntegerField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    group_by = serializers.ChoiceField(
        choices=['status', 'priority', 'assignee', 'date', 'tag'],
        required=False,
        default='status'
    )