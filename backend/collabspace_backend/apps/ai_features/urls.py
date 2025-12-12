from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskAIView, MeetingAIView, AnalyticsAIView, 
    CodeAIView, AssistantView, AIUsageView, AITemplateViewSet
)

app_name = 'ai_features'

# Initialize routers
router = DefaultRouter()
router.register('templates', AITemplateViewSet, basename='ai-template')
router.register('tasks', TaskAIView, basename='ai-task')
router.register('meetings', MeetingAIView, basename='ai-meeting')
router.register('analytics', AnalyticsAIView, basename='ai-analytics')
router.register('code', CodeAIView, basename='ai-code')  # Added Code ViewSet
router.register('assistant', AssistantView, basename='ai-assistant')
router.register('usage', AIUsageView, basename='ai-usage')


urlpatterns = [
    # Router includes list/retrieve/create/update for ViewSets
    path('', include(router.urls)),
    
    # --- Task AI Routes ---
    path('tasks/summarize/', TaskAIView.as_view({'post': 'summarize'}), name='task-summarize'),
    path('tasks/auto-create/', TaskAIView.as_view({'post': 'auto_create'}), name='task-auto-create'),
    path('tasks/breakdown/', TaskAIView.as_view({'post': 'breakdown'}), name='task-breakdown'),
    path('tasks/estimate/', TaskAIView.as_view({'post': 'estimate'}), name='task-estimate'),
    path('tasks/priority/', TaskAIView.as_view({'post': 'priority'}), name='task-priority'),
    path('tasks/suggest-assignee/', TaskAIView.as_view({'post': 'suggest_assignee'}), name='task-suggest-assignee'),
    path('tasks/dependencies/', TaskAIView.as_view({'post': 'dependencies'}), name='task-dependencies'),
    path('tasks/tags/', TaskAIView.as_view({'post': 'tags'}), name='task-tags'),
    path('tasks/status-update/', TaskAIView.as_view({'post': 'status_update'}), name='task-status-update'),
    
    # --- Meeting AI Routes ---
    path('meetings/summarize/', MeetingAIView.as_view({'post': 'summarize'}), name='meeting-summarize'),
    path('meetings/action-items/', MeetingAIView.as_view({'post': 'action_items'}), name='meeting-action-items'),
    path('meetings/sentiment/', MeetingAIView.as_view({'post': 'sentiment'}), name='meeting-sentiment'),
    path('meetings/decisions/', MeetingAIView.as_view({'post': 'decisions'}), name='meeting-decisions'),
    path('meetings/follow-up-email/', MeetingAIView.as_view({'post': 'follow_up_email'}), name='meeting-email'),
    
    # --- Code AI Routes ---
    path('code/review/', CodeAIView.as_view({'post': 'review'}), name='code-review'),
    path('code/generate/', CodeAIView.as_view({'post': 'generate'}), name='code-generate'),
    path('code/explain/', CodeAIView.as_view({'post': 'explain'}), name='code-explain'),
    path('code/debug/', CodeAIView.as_view({'post': 'debug'}), name='code-debug'),
    path('code/tests/', CodeAIView.as_view({'post': 'tests'}), name='code-tests'),
    path('code/refactor/', CodeAIView.as_view({'post': 'refactor'}), name='code-refactor'),
    path('code/convert/', CodeAIView.as_view({'post': 'convert'}), name='code-convert'),

    # --- Analytics AI Routes ---
    path('analytics/project-forecast/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'project_forecast'}), name='analytics-project-forecast'),
    path('analytics/burnout-detection/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'burnout_detection'}), name='analytics-burnout-detection'),
    path('analytics/velocity/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'velocity'}), name='analytics-velocity'),
    path('analytics/resource-optimizer/', AnalyticsAIView.as_view({'post': 'resource_optimizer'}), name='analytics-resource-optimizer'),
    path('analytics/bottlenecks/<uuid:pk>/', AnalyticsAIView.as_view({'get': 'bottlenecks'}), name='analytics-bottlenecks'),
    
    # --- Assistant Routes ---
    path('assistant/chat/', AssistantView.as_view({'post': 'chat'}), name='assistant-chat'),
    path('assistant/search/', AssistantView.as_view({'post': 'search'}), name='assistant-search'),
    
    # --- Usage Routes ---
    path('usage/', AIUsageView.as_view({'get': 'usage'}), name='usage-user'),
    path('usage/workspace/<uuid:pk>/', AIUsageView.as_view({'get': 'workspace_usage'}), name='usage-workspace'),
    path('usage/quota/', AIUsageView.as_view({'get': 'quota'}), name='usage-quota'),
]