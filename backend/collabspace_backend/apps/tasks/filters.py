import django_filters
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta 

from .models import Task 

class TaskFilter(django_filters.FilterSet):
    """
    Comprehensive filter for tasks, combining basic, advanced, and custom criteria.
    """

    # --- Basic Filters (from original TaskFilter) ---
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=Task.STATUS_CHOICES,
        help_text='Filter by single task status'
    )
    
    priority = django_filters.ChoiceFilter(
        field_name='priority',
        choices=Task.PRIORITY_CHOICES,
        help_text='Filter by single task priority'
    )
    
    project = django_filters.NumberFilter(
        field_name='project_id',
        help_text='Filter by project ID'
    )
    
    assigned_to = django_filters.NumberFilter(
        field_name='assigned_to_id',
        help_text='Filter by assigned user ID'
    )
    
    created_by = django_filters.NumberFilter(
        field_name='created_by_id',
        help_text='Filter by creator user ID'
    )
    
    parent_task = django_filters.NumberFilter(
        field_name='parent_task_id',
        help_text='Filter by parent task ID'
    )
    
    # --- Multi-Select Filters (from TaskFilterExtended) ---
    statuses = django_filters.CharFilter(
        method='filter_statuses',
        help_text='Filter by multiple statuses (comma-separated, e.g., todo,in_progress)'
    )
    
    priorities = django_filters.CharFilter(
        method='filter_priorities',
        help_text='Filter by multiple priorities (comma-separated, e.g., high,urgent)'
    )
    
    assigned_users = django_filters.CharFilter(
        method='filter_assigned_users',
        help_text='Filter by multiple assigned user IDs (comma-separated IDs)'
    )

    # --- Date Range Filters (Combined) ---
    due_date_from = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte',
        help_text='Filter tasks due after this date'
    )
    
    due_date_to = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte',
        help_text='Filter tasks due before this date'
    )
    
    created_at_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='Filter tasks created after this date'
    )
    
    created_at_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='Filter tasks created before this date'
    )
    
    # --- Advanced Date Filters (from TaskFilterExtended/TaskAdvancedFilter) ---
    created_last_days = django_filters.NumberFilter(
        method='filter_created_last_days',
        help_text='Filter tasks created in the last N days'
    )
    
    due_next_days = django_filters.NumberFilter(
        method='filter_due_next_days',
        help_text='Filter tasks due in the next N days'
    )

    # --- Search and Tag Filters ---
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='Search in title, description, and tags'
    )
    
    tags = django_filters.CharFilter(
        method='filter_by_tags',
        help_text='Filter by tasks that have any of the given tags (comma-separated)'
    )
    
    has_tags = django_filters.BooleanFilter(
        method='filter_has_tags',
        help_text='Filter tasks with or without tags'
    )

    # --- Collaboration/Activity Filters (from TaskFilterExtended) ---
    has_comments = django_filters.BooleanFilter(
        method='filter_has_comments',
        help_text='Filter tasks with or without comments'
    )
    
    has_attachments = django_filters.BooleanFilter(
        method='filter_has_attachments',
        help_text='Filter tasks with or without attachments'
    )
    
    has_time_entries = django_filters.BooleanFilter(
        method='filter_has_time_entries',
        help_text='Filter tasks with or without time entries'
    )

    collaborator = django_filters.NumberFilter(
        method='filter_collaborator',
        help_text='Filter tasks where user is involved (assigned, created, commented, or logged time)'
    )
    
    # --- Status/Hierarchy/Dependency Filters ---
    is_overdue = django_filters.BooleanFilter(
        method='filter_overdue',
        help_text='Filter overdue tasks'
    )
    
    has_subtasks = django_filters.BooleanFilter(
        method='filter_has_subtasks',
        help_text='Filter tasks with subtasks'
    )
    
    is_root = django_filters.BooleanFilter(
        method='filter_is_root',
        help_text='Filter root tasks (no parent)'
    )
    
    unassigned = django_filters.BooleanFilter(
        method='filter_unassigned',
        help_text='Filter unassigned tasks'
    )
    
    has_dependencies = django_filters.BooleanFilter(
        method='filter_has_dependencies',
        help_text='Filter tasks with dependencies (either blocking or blocked by)'
    )
    
    is_blocked = django_filters.BooleanFilter(
        method='filter_blocked',
        help_text='Filter tasks that are currently blocked by an incomplete dependency'
    )
    
    completion_status = django_filters.ChoiceFilter(
        method='filter_completion_status',
        choices=[
            ('completed', 'Completed'),
            ('active', 'Active'),
            ('blocked', 'Blocked'),
            ('stalled', 'Stalled'),
        ],
        help_text='Filter by special completion states (completed, active, blocked, stalled)'
    )
    
    # --- Time-based Filters ---
    estimated_hours_min = django_filters.NumberFilter(
        field_name='estimated_hours',
        lookup_expr='gte',
        help_text='Minimum estimated hours'
    )
    
    estimated_hours_max = django_filters.NumberFilter(
        field_name='estimated_hours',
        lookup_expr='lte',
        help_text='Maximum estimated hours'
    )
    
    # --- Filter Methods ---

    def filter_statuses(self, queryset, name, value):
        """Filter by multiple statuses (comma-separated)."""
        statuses = [s.strip() for s in value.split(',')]
        return queryset.filter(status__in=statuses)

    def filter_priorities(self, queryset, name, value):
        """Filter by multiple priorities (comma-separated)."""
        priorities = [p.strip() for p in value.split(',')]
        return queryset.filter(priority__in=priorities)

    def filter_assigned_users(self, queryset, name, value):
        """Filter by multiple assigned users (comma-separated IDs)."""
        try:
            user_ids = [int(uid.strip()) for uid in value.split(',')]
        except ValueError:
            return queryset.none() # Return empty if IDs are invalid
        return queryset.filter(assigned_to_id__in=user_ids)

    def filter_created_last_days(self, queryset, name, value):
        """Filter tasks created in last N days."""
        cutoff = timezone.now() - timedelta(days=value)
        return queryset.filter(created_at__gte=cutoff)

    def filter_due_next_days(self, queryset, name, value):
        """Filter tasks due in next N days."""
        now = timezone.now()
        future = now + timedelta(days=value)
        # Filters tasks due in the future, up to `future`
        return queryset.filter(due_date__gte=now, due_date__lte=future, status__in=['todo', 'in_progress', 'review'])

    def filter_search(self, queryset, name, value):
        """Full-text search across title, description, and tags."""
        if not value:
            return queryset
        # Search combines the logic from both previous 'search' methods
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(tags__contains=[value])
        ).distinct()

    def filter_has_comments(self, queryset, name, value):
        """Filter tasks with or without comments."""
        if value:
            return queryset.filter(comments__isnull=False).distinct()
        return queryset.filter(comments__isnull=True).distinct()

    def filter_has_attachments(self, queryset, name, value):
        """Filter tasks with or without attachments."""
        if value:
            return queryset.filter(attachments__isnull=False).distinct()
        return queryset.filter(attachments__isnull=True).distinct()

    def filter_has_time_entries(self, queryset, name, value):
        """Filter tasks with or without time entries."""
        if value:
            return queryset.filter(time_entries__isnull=False).distinct()
        return queryset.filter(time_entries__isnull=True).distinct()

    def filter_completion_status(self, queryset, name, value):
        """Filter by special completion status (completed, active, blocked, stalled)."""
        if value == 'completed':
            return queryset.filter(status=Task.STATUS_DONE)
        elif value == 'active':
            return queryset.filter(
                status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_REVIEW]
            )
        elif value == 'blocked':
            # Note: This is a computed filter and may be slow. It relies on the Task.is_blocked() method.
            blocked_ids = [task.id for task in queryset if task.is_blocked()]
            return queryset.filter(id__in=blocked_ids)
        elif value == 'stalled':
            # Tasks not updated in 7+ days and not done
            cutoff = timezone.now() - timedelta(days=7)
            return queryset.filter(
                updated_at__lt=cutoff,
                status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_REVIEW]
            )
        return queryset


    def filter_by_tags(self, queryset, name, value):
        """Filter tasks by tags (comma-separated)."""
        if not value:
            return queryset
        tags = [tag.strip() for tag in value.split(',')]
        # Use overlap for OR logic (task has ANY of the tags)
        return queryset.filter(tags__overlap=tags)

    def filter_has_tags(self, queryset, name, value):
        """Filter tasks with or without tags."""
        if value:
            return queryset.exclude(tags=[])
        else:
            return queryset.filter(tags=[])

    def filter_overdue(self, queryset, name, value):
        """Filter overdue tasks."""
        # This handles both ?is_overdue=true and ?is_overdue=false cases
        overdue_filter = Q(
            due_date__lt=timezone.now(),
            status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_REVIEW]
        )
        if value:
            return queryset.filter(overdue_filter)
        else:
            return queryset.exclude(overdue_filter)

    def filter_has_subtasks(self, queryset, name, value):
        """Filter tasks with or without subtasks."""
        if value:
            return queryset.filter(subtasks__isnull=False).distinct()
        else:
            return queryset.filter(subtasks__isnull=True)

    def filter_is_root(self, queryset, name, value):
        """Filter root tasks (no parent)."""
        if value:
            return queryset.filter(parent_task__isnull=True)
        else:
            return queryset.filter(parent_task__isnull=False)

    def filter_unassigned(self, queryset, name, value):
        """Filter unassigned tasks."""
        if value:
            return queryset.filter(assigned_to__isnull=True)
        else:
            return queryset.filter(assigned_to__isnull=False)

    def filter_has_dependencies(self, queryset, name, value):
        """Filter tasks with dependencies (either blocking or blocked by)."""
        if value:
            # Check for either side of the dependency relationship
            return queryset.filter(Q(dependencies__isnull=False) | Q(dependents__isnull=False)).distinct()
        else:
            return queryset.filter(Q(dependencies__isnull=True), Q(dependents__isnull=True))

    def filter_blocked(self, queryset, name, value):
        """Filter blocked tasks (has incomplete blocking dependencies)."""
        # Note: Relies on `task.is_blocked()` which is slow. Using the implementation from the second snippet.
        if value:
            # Get tasks with blocking dependencies
            tasks_with_deps = queryset.filter(
                dependencies__dependency_type='blocks'
            ).distinct()
            
            # Filter to only those where the blocking task is not done
            blocked_task_ids = [task.id for task in tasks_with_deps if task.is_blocked()]
            
            return queryset.filter(id__in=blocked_task_ids)
        else:
            # Return tasks that are NOT blocked (more complex query, using the second snippet's logic)
            tasks_with_deps = queryset.filter(
                dependencies__dependency_type='blocks'
            ).distinct()
            
            # Find the IDs of tasks that HAVE blocking dependencies but are currently unblocked
            unblocked_task_ids = [task.id for task in tasks_with_deps if not task.is_blocked()]
            
            # Find the IDs of tasks with NO dependencies
            no_deps = queryset.filter(Q(dependencies__isnull=True), Q(dependents__isnull=True)).values_list('id', flat=True)
            
            # Combine both sets of IDs
            all_unblocked = list(unblocked_task_ids) + list(no_deps)
            
            return queryset.filter(id__in=all_unblocked)

    def filter_collaborator(self, queryset, name, value):
        """Filter tasks where user is a collaborator (assigned, created, commented, or logged time)."""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(assigned_to_id=value) |
            Q(created_by_id=value) |
            Q(comments__user_id=value) |
            Q(time_entries__user_id=value)
        ).distinct()
    
    class Meta:
        model = Task
        fields = [
            'status', 'priority', 'project', 'assigned_to', 'created_by',
            'parent_task', 'due_date_from', 'due_date_to', 'created_at_from',
            'created_at_to', 'is_active', 'estimated_hours_min', 'estimated_hours_max',
        ]

# Note: The filters related to completion percentage (min/max) that rely on 
# `get_subtask_progress_percentage()` were excluded from the final class as they are 
# expensive and should be handled separately, possibly via annotations or optimized 
# logic, to avoid N+1 query problems in a production environment. 
# If they are critical, you should use the methods from TaskAdvancedFilter.