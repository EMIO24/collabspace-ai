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
    TaskTemplateViewSet,
    TaskAnalyticsViewSet  # Ensure this is imported
)

# Initialize router and register all ViewSets
router = DefaultRouter()

# 1. Core Task Management
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', TaskCommentViewSet, basename='comment')
router.register(r'attachments', TaskAttachmentViewSet, basename='attachment')
router.register(r'time-entries', TimeEntryViewSet, basename='time-entry')
router.register(r'templates', TaskTemplateViewSet, basename='template')

# 2. AI & Analytics Dashboard
# This creates endpoints like: 
# - GET /api/tasks/ai/analytics/velocity/
# - GET /api/tasks/ai/analytics/burnout-detection/
# - GET /api/tasks/ai/analytics/bottlenecks/
router.register(r'ai/analytics', TaskAnalyticsViewSet, basename='task-analytics')

# Define URL patterns
urlpatterns = [
    # Custom standalone endpoint for task statistics (Legacy/Simple stats)
    # Accessible at: /api/tasks/stats/
    path('stats/', TaskStatsView.as_view(), name='task-stats'),
    
    # Include all router-generated URLs (CRUD for tasks, comments, etc.)
    path('', include(router.urls)),
]