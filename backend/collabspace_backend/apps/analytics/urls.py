# Note: In a real Django project, this would import from django.urls import path
class MockPath:
    def __init__(self, route, view):
        self.route = route
        self.view = view
    def __repr__(self):
        return f"path('{self.route}', {self.view.__name__})"

def path(route, view):
    return MockPath(route, view)

from .views import (
    WorkspaceAnalyticsView, ProjectAnalyticsView, TeamProductivityView,
    BurndownChartView, VelocityChartView, TimeTrackingReportView
)

urlpatterns = [
    # Metrics
    path('workspace/<int:workspace_id>/metrics/', WorkspaceAnalyticsView.get, name='workspace-metrics'),
    path('project/<int:project_id>/metrics/', ProjectAnalyticsView.get, name='project-metrics'),
    path('workspace/<int:workspace_id>/productivity/', TeamProductivityView.get, name='team-productivity'),

    # Charts
    path('project/<int:project_id>/burndown/', BurndownChartView.get, name='burndown-chart'),
    path('team/<str:team_id>/velocity/', VelocityChartView.get, name='velocity-chart'), # Using str for team_id

    # Reports/Exports
    path('reports/time_tracking/', TimeTrackingReportView.get, name='time-tracking-report'),
]

# Example of how the URL patterns look:
print("\n--- Analytics URL Patterns ---")
for url_pattern in urlpatterns:
    print(url_pattern)