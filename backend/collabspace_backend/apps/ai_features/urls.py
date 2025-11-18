# Mock imports for Django routing
def path(route, view_func):
    return f"/{route} -> {view_func.__name__}"
def include(app_name):
    return app_name

from .views import TaskAIView, MeetingAIView, CodeAIView, AnalyticsAIView, AssistantView

# Initialize view instances (simplified for this mock file)
task_views = TaskAIView()
meeting_views = MeetingAIView()
code_views = CodeAIView()
analytics_views = AnalyticsAIView()
assistant_views = AssistantView()

urlpatterns = [
    # --- Task AI Endpoints ---
    path("tasks/summarize/", task_views.post_summarize),
    path("tasks/auto-create/", task_views.post_autocreate),
    path("tasks/breakdown/", task_views.post_breakdown),
    path("tasks/estimate/", task_views.post_estimate),
    path("tasks/priority/", task_views.post_priority),
    
    # --- Meeting AI Endpoints ---
    path("meetings/transcribe/", meeting_views.post_transcribe),
    path("meetings/summarize/", meeting_views.post_summarize),
    path("meetings/action-items/", meeting_views.post_action_items),
    
    # --- Code AI Endpoints ---
    path("code/review/", code_views.post_review),
    path("code/generate/", code_views.post_generate),
    path("code/explain/", code_views.post_explain),
    
    # --- Analytics AI Endpoints ---
    path("analytics/project-forecast/<str:id>/", analytics_views.get_project_forecast),
    path("analytics/burnout-detection/", analytics_views.get_burnout_detection),
    path("analytics/velocity/", analytics_views.get_velocity),
    
    # --- Assistant AI Endpoints ---
    path("assistant/chat/", assistant_views.post_chat),
    path("assistant/search/", assistant_views.post_search),
]