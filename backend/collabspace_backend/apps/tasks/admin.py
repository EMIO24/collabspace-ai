"""
CollabSpace AI - Tasks Module Admin
Comprehensive Django admin configuration for all task-related models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    Task, TaskDependency, TaskComment, TaskAttachment, 
    TimeEntry, TaskTemplate
)

# --- INLINE ADMIN CLASSES ---

class TaskDependencyInline(admin.TabularInline):
    model = TaskDependency
    fk_name = 'task'
    extra = 1
    autocomplete_fields = ['depends_on']
    verbose_name_plural = 'Dependencies'


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ['user', 'created_at']
    fields = ['user', 'content', 'parent_comment', 'created_at']


class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    readonly_fields = ['uploaded_by', 'file_size_display', 'created_at']
    fields = ['file_name', 'file_url', 'file_type', 'file_size_display', 'uploaded_by', 'created_at']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display() if obj.pk else '-'
    file_size_display.short_description = 'File Size'


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    readonly_fields = ['user', 'created_at']
    fields = ['user', 'hours', 'description', 'date', 'created_at']


# --- TASK ADMIN CONFIGURATION ---

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'status_badge', 'priority_badge', 'project_link',
        'assigned_to_link', 'due_date_display', 'progress_display',
        'is_overdue_display', 'created_at'
    ]
    
    list_filter = [
        'status', 'priority', 'is_active', 'project',
        ('due_date', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'title', 'description', 'tags',
        'assigned_to__username', 'created_by__username', 'project__name'
    ]
    
    autocomplete_fields = ['project', 'assigned_to', 'created_by', 'parent_task']
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by',
        'actual_hours_display', 'time_remaining_display',
        'subtask_progress', 'collaborators_display',
        'blocking_tasks_display', 'blocked_tasks_display'
    ]
    
    fieldsets = [
        ('Basic Information', {'fields': ['project', 'title', 'description', 'parent_task']}),
        ('Status & Priority', {'fields': ['status', 'priority', 'is_active']}),
        ('Assignment', {'fields': ['assigned_to', 'created_by']}),
        ('Time Tracking', {'fields': ['due_date', 'estimated_hours', 'actual_hours_display', 'time_remaining_display']}),
        ('Organization', {'fields': ['tags', 'position']}),
        ('Progress', {'fields': ['subtask_progress', 'collaborators_display', 'blocking_tasks_display', 'blocked_tasks_display'], 'classes': ['collapse']}),
        ('Metadata', {'fields': ['metadata', 'created_at', 'updated_at'], 'classes': ['collapse']}),
    ]
    
    inlines = [
        TaskDependencyInline, TaskCommentInline, TaskAttachmentInline, TimeEntryInline
    ]
    
    actions = [
        'mark_as_todo', 'mark_as_in_progress', 'mark_as_review',
        'mark_as_done', 'set_high_priority', 'set_medium_priority',
        'set_low_priority', 'duplicate_tasks'
    ]
    
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'project', 'assigned_to', 'created_by', 'parent_task'
        ).prefetch_related(
            'subtasks', 'dependencies', 'comments', 'time_entries'
        )
    
    def status_badge(self, obj):
        colors = {'todo': '#6c757d', 'in_progress': '#007bff', 'review': '#ffc107', 'done': '#28a745'}
        color = colors.get(obj.status, '#6c757d')
        return format_html('<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {'low': '#28a745', 'medium': '#ffc107', 'high': '#fd7e14', 'urgent': '#dc3545'}
        color = colors.get(obj.priority, '#6c757d')
        return format_html('<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>', color, obj.get_priority_display())
    priority_badge.short_description = 'Priority'
    
    def project_link(self, obj):
        if obj.project:
            url = reverse('admin:projects_project_change', args=[obj.project.pk])
            return format_html('<a href="{}">{}</a>', url, obj.project.name)
        return '-'
    project_link.short_description = 'Project'
    
    def assigned_to_link(self, obj):
        if obj.assigned_to:
            url = reverse('admin:auth_user_change', args=[obj.assigned_to.pk])
            return format_html('<a href="{}">{}</a>', url, obj.assigned_to.username)
        return format_html('<span style="color: #dc3545;">Unassigned</span>')
    assigned_to_link.short_description = 'Assigned To'
    
    def due_date_display(self, obj):
        if not obj.due_date: return '-'
        
        display = obj.due_date.strftime('%Y-%m-%d %H:%M')
        
        if hasattr(obj, 'is_overdue') and obj.is_overdue():
            return format_html('<span style="color: #dc3545; font-weight: bold;">{} (Overdue)</span>', display)
        
        if obj.due_date > timezone.now():
            days_until_due = (obj.due_date - timezone.now()).days
            if 0 <= days_until_due <= 3:
                return format_html('<span style="color: #ffc107; font-weight: bold;">{} ({} days)</span>', display, days_until_due)
        
        return display
    due_date_display.short_description = 'Due Date'
    
    def progress_display(self, obj):
        if obj.get_subtask_count() == 0: return '-'
        
        percentage = obj.get_subtask_progress_percentage()
        color = '#28a745' if percentage == 100 else '#007bff'
        
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; padding: 2px; border-radius: 3px; font-size: 10px;">{}%</div></div>',
            percentage, color, int(percentage)
        )
    progress_display.short_description = 'Progress'
    
    def is_overdue_display(self, obj):
        if hasattr(obj, 'is_overdue') and obj.is_overdue():
            return format_html('<span style="color: #dc3545;">⚠ Overdue</span>')
        return format_html('<span style="color: #28a745;">✓ On Track</span>')
    is_overdue_display.short_description = 'Status'
    
    def actual_hours_display(self, obj):
        return f"{obj.actual_hours} hours"
    actual_hours_display.short_description = 'Actual Hours'
    
    def time_remaining_display(self, obj):
        remaining = obj.get_time_remaining()
        if remaining is None: return 'Not estimated'
        if remaining <= 0:
            return format_html('<span style="color: #dc3545;">Over budget</span>')
        return f"{remaining} hours"
    time_remaining_display.short_description = 'Time Remaining'
    
    def subtask_progress(self, obj):
        count = obj.get_subtask_count()
        if count == 0: return 'No subtasks'
        completed = obj.get_completed_subtasks_count()
        percentage = obj.get_subtask_progress_percentage()
        return format_html('{} / {} subtasks completed ({}%)', completed, count, int(percentage))
    subtask_progress.short_description = 'Subtask Progress'
    
    def collaborators_display(self, obj):
        collaborators = obj.get_collaborators()
        if not collaborators: return 'None'
        names = [user.username for user in collaborators[:5]]
        result = ', '.join(names)
        if len(collaborators) > 5:
            result += f' (+{len(collaborators) - 5} more)'
        return result
    collaborators_display.short_description = 'Collaborators'
    
    def _dependency_list_display(self, tasks):
        if not tasks: return 'None'
        links = []
        for task in tasks[:3]:
            url = reverse('admin:tasks_task_change', args=[task.pk])
            links.append(format_html('<a href="{}">{}</a>', url, task.title))
        result = ', '.join(links)
        if len(tasks) > 3:
            result += f' (+{len(tasks) - 3} more)'
        return format_html(result)

    def blocking_tasks_display(self, obj):
        return self._dependency_list_display(obj.get_blocking_tasks())
    blocking_tasks_display.short_description = 'Blocking Tasks'
    
    def blocked_tasks_display(self, obj):
        return self._dependency_list_display(obj.get_blocked_tasks())
    blocked_tasks_display.short_description = 'Blocked Tasks'
    
    # Actions
    def mark_as_todo(self, request, queryset):
        updated = queryset.update(status=Task.STATUS_TODO)
        self.message_user(request, f'{updated} tasks marked as To Do')
    mark_as_todo.short_description = 'Mark as To Do'
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status=Task.STATUS_IN_PROGRESS)
        self.message_user(request, f'{updated} tasks marked as In Progress')
    mark_as_in_progress.short_description = 'Mark as In Progress'
    
    def mark_as_review(self, request, queryset):
        updated = queryset.update(status=Task.STATUS_REVIEW)
        self.message_user(request, f'{updated} tasks marked as Review')
    mark_as_review.short_description = 'Mark as Review'
    
    def mark_as_done(self, request, queryset):
        updated = queryset.update(status=Task.STATUS_DONE)
        self.message_user(request, f'{updated} tasks marked as Done')
    mark_as_done.short_description = 'Mark as Done'
    
    def set_high_priority(self, request, queryset):
        updated = queryset.update(priority=Task.PRIORITY_HIGH)
        self.message_user(request, f'{updated} tasks set to High priority')
    set_high_priority.short_description = 'Set High Priority'
    
    def set_medium_priority(self, request, queryset):
        updated = queryset.update(priority=Task.PRIORITY_MEDIUM)
        self.message_user(request, f'{updated} tasks set to Medium priority')
    set_medium_priority.short_description = 'Set Medium Priority'
    
    def set_low_priority(self, request, queryset):
        updated = queryset.update(priority=Task.PRIORITY_LOW)
        self.message_user(request, f'{updated} tasks set to Low priority')
    set_low_priority.short_description = 'Set Low Priority'


# --- TEMPLATE ADMIN CONFIGURATION ---

@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'default_priority', 'is_public',
        'usage_count', 'created_by_link', 'created_at'
    ]

    list_filter = ['category', 'default_priority', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'category', 'title_template']
    autocomplete_fields = ['created_by']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']

    fieldsets = [
        ('Basic Information', {'fields': ['name', 'description', 'category', 'is_public']}),
        ('Template Fields', {'fields': ['title_template', 'description_template', 'default_priority', 'default_estimated_hours', 'default_tags']}),
        ('Advanced', {'fields': ['subtask_templates', 'checklist_items'], 'classes': ['collapse']}),
        ('Metadata', {'fields': ['created_by', 'usage_count', 'created_at', 'updated_at'], 'classes': ['collapse']}),
    ]

    actions = ['make_public', 'make_private']

    def created_by_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.created_by.pk])
        return format_html('<a href="{}">{}</a>', url, obj.created_by.username)
    created_by_link.short_description = 'Created By'

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} templates made public')
    make_public.short_description = 'Make public'

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} templates made private')
    make_private.short_description = 'Make private'


# --- SUPPORTING MODEL ADMIN CONFIGURATIONS ---

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'task_link', 'user_link', 'created_at', 'is_active']
    list_filter = ['is_active', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['content', 'user__username', 'task__title']
    autocomplete_fields = ['task', 'user', 'parent_comment']
    readonly_fields = ['created_at', 'updated_at', 'thread_depth_display']
    date_hierarchy = 'created_at'
    
    def short_content(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    short_content.short_description = 'Content'
    
    def task_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.task.pk])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def thread_depth_display(self, obj):
        depth = obj.get_thread_depth()
        return f"Level {depth}"
    thread_depth_display.short_description = 'Thread Depth'


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'file_name', 'task_link', 'file_type', 'file_size_display',
        'uploaded_by_link', 'created_at'
    ]
    list_filter = ['file_type', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['file_name', 'task__title', 'uploaded_by__username']
    autocomplete_fields = ['task', 'uploaded_by']
    readonly_fields = ['created_at', 'updated_at', 'file_size_display']
    date_hierarchy = 'created_at'
    
    def task_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.task.pk])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def uploaded_by_link(self, obj):
        if obj.uploaded_by:
            url = reverse('admin:auth_user_change', args=[obj.uploaded_by.pk])
            return format_html('<a href="{}">{}</a>', url, obj.uploaded_by.username)
        return '-'
    uploaded_by_link.short_description = 'Uploaded By'
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = [
        'task_link', 'user_link', 'hours', 'date', 'created_at'
    ]
    list_filter = [
        ('date', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter)
    ]
    search_fields = ['task__title', 'user__username', 'description']
    autocomplete_fields = ['task', 'user']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    def task_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.task.pk])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = [
        'task_link', 'dependency_type', 'depends_on_link', 'created_at'
    ]
    list_filter = ['dependency_type', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['task__title', 'depends_on__title']
    autocomplete_fields = ['task', 'depends_on']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def task_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.task.pk])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def depends_on_link(self, obj):
        url = reverse('admin:tasks_task_change', args=[obj.depends_on.pk])
        return format_html('<a href="{}">{}</a>', url, obj.depends_on.title)
    depends_on_link.short_description = 'Depends On'