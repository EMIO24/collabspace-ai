from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

# Example admin action
def mark_as_active(modeladmin, request, queryset):
    """
    Admin action to mark selected items as active.
    """
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} items marked as active.")

mark_as_active.short_description = "Mark selected items as active"

# Register your core models here
@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at", "is_active")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "owner__username")
    actions = [mark_as_active]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "workspace__name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "assigned_to", "due_date")
    list_filter = ("status", "priority", "due_date")
    search_fields = ("title", "project__title", "assigned_to__username")
