from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskAIView, MeetingAIView, AnalyticsAIView, AssistantView, AIUsageView, AITemplateViewSet

app_name = 'ai_features'

# Initialize routers for ModelViewSets and GenericViewSets
router = DefaultRouter()
# Template ViewSet
router.register('templates', AITemplateViewSet, basename='ai-template')
# Generic ViewSets for bulk/custom actions
router.register('tasks', TaskAIView, basename='ai-task')
router.register('meetings', MeetingAIView, basename='ai-meeting')
router.register('analytics', AnalyticsAIView, basename='ai-analytics')
router.register('assistant', AssistantView, basename='ai-assistant')
router.register('usage', AIUsageView, basename='ai-usage')


# The urlpatterns use the standard DRF router output, plus custom routes for clarity
urlpatterns = [
    # Router includes list/retrieve/create/update for AITemplateViewSet
    path('', include(router.urls)),
    
    # Custom/Specific Task AI Routes (using GenericViewSet actions)
    path('tasks/summarize/', TaskAIView.as_view({'post': 'summarize'}), name='task-summarize'),
    path('tasks/auto-create/', TaskAIView.as_view({'post': 'auto_create'}), name='task-auto-create'),
    path('tasks/breakdown/', TaskAIView.as_view({'post': 'breakdown'}), name='task-breakdown'),
    path('tasks/estimate/', TaskAIView.as_view({'post': 'estimate'}), name='task-estimate'),
    path('tasks/priority/', TaskAIView.as_view({'post': 'priority'}), name='task-priority'),
    path('tasks/suggest-assignee/', TaskAIView.as_view({'post': 'suggest_assignee'}), name='task-suggest-assignee'),
    
    # Custom/Specific Meeting AI Routes
    path('meetings/summarize/', MeetingAIView.as_view({'post': 'summarize'}), name='meeting-summarize'),
    path('meetings/action-items/', MeetingAIView.as_view({'post': 'action_items'}), name='meeting-action-items'),
    path('meetings/sentiment/', MeetingAIView.as_view({'post': 'sentiment'}), name='meeting-sentiment'),
    
    # Custom/Specific Analytics AI Routes (using path() for detail routes)
    path('analytics/project-forecast/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'project_forecast'}), name='analytics-project-forecast'),
    path('analytics/burnout-detection/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'burnout_detection'}), name='analytics-burnout-detection'),
    path('analytics/velocity/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'velocity'}), name='analytics-velocity'),
    path('analytics/resource-optimizer/', AnalyticsAIView.as_view({'post': 'resource_optimizer'}), name='analytics-resource-optimizer'),
    path('analytics/bottlenecks/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'bottlenecks'}), name='analytics-bottlenecks'),
    
    # Custom/Specific Assistant Routes
    path('assistant/chat/', AssistantView.as_view({'post': 'chat'}), name='assistant-chat'),
    path('assistant/search/', AssistantView.as_view({'post': 'search'}), name='assistant-search'),
    
    # Custom/Specific Usage Routes
    path('usage/', AIUsageView.as_view({'get': 'usage'}), name='usage-user'),
    path('usage/workspace/<uuid:pk>/', AIUsageView.as_view({'get': 'workspace_usage'}), name='usage-workspace'),
    path('usage/quota/', AIUsageView.as_view({'get': 'quota'}), name='usage-quota'),
]