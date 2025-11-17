"""
CollabSpace AI - Tasks Module URLs
Routing configuration for all task-related API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TaskViewSet, 
    TaskCommentViewSet, 
    TaskAttachmentViewSet,
    TimeEntryViewSet, 
    TaskStatsView,
    TaskTemplateViewSet
)

app_name = 'tasks'

# Initialize router and register all ViewSets
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', TaskCommentViewSet, basename='comment')
router.register(r'attachments', TaskAttachmentViewSet, basename='attachment')
router.register(r'time-entries', TimeEntryViewSet, basename='time-entry')
router.register(r'templates', TaskTemplateViewSet, basename='template')

# Define URL patterns
urlpatterns = [
    # Include all router-generated URLs (CRUD for tasks, comments, etc.)
    path('', include(router.urls)),
    
    # Custom standalone endpoint for task statistics
    path('tasks/stats/', TaskStatsView.as_view(), name='task-stats'),
]