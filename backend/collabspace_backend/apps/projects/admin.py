from django.contrib import admin
from .models import (
    Project, 
    ProjectMember, 
    ProjectLabel, 
    ProjectTemplate, 
    ProjectActivity
)

# --- Project Admin ---

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'workspace', 
        'owner', 
        'status', 
        'priority', 
        'progress', 
        'member_count', 
        'is_public', 
        'created_at'
    )
    list_filter = ('workspace', 'status', 'priority', 'is_public')
    search_fields = ('name', 'description', 'slug')
    readonly_fields = (
        'id', 
        'slug', 
        'task_count', 
        'completed_task_count', 
        'member_count', 
        'progress', 
        'created_at', 
        'updated_at'
    )
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'description', 'workspace', 'owner')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'start_date', 'end_date')
        }),
        ('Customization', {
            'fields': ('color', 'icon', 'is_public', 'settings')
        }),
        ('Performance & Metrics', {
            'fields': ('member_count', 'task_count', 'completed_task_count', 'progress')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

# --- Project Member Admin ---

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'added_at', 'added_by')
    list_filter = ('project', 'role', 'added_at')
    search_fields = ('user__email', 'project__name')
    raw_id_fields = ('project', 'user', 'added_by') # Use raw_id_fields for FKs to prevent slow-loading admin
    readonly_fields = ('added_at', 'created_at', 'updated_at')

# --- Project Label Admin ---

@admin.register(ProjectLabel)
class ProjectLabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'color', 'created_by')
    list_filter = ('project',)
    search_fields = ('name', 'description')
    raw_id_fields = ('project', 'created_by')
    readonly_fields = ('created_at', 'updated_at')

# --- Project Template Admin ---

@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'workspace', 'created_by', 'is_public', 'use_count', 'created_at')
    list_filter = ('is_public', 'workspace')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'use_count', 'created_at', 'updated_at')
    raw_id_fields = ('workspace', 'created_by')

# --- Project Activity Admin ---

@admin.register(ProjectActivity)
class ProjectActivityAdmin(admin.ModelAdmin):
    list_display = ('project', 'action', 'user', 'created_at')
    list_filter = ('project', 'action', 'created_at')
    search_fields = ('description', 'project__name', 'user__email')
    raw_id_fields = ('project', 'user')
    readonly_fields = ('created_at', 'updated_at')