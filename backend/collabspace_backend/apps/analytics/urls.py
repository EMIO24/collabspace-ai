# apps/analytics/urls.py

from django.urls import path
from .views import (
    WorkspaceAnalyticsView,
    ProjectAnalyticsView,
    TeamProductivityView,
    BurndownChartView,
    VelocityChartView,
    TimeTrackingReportView
)

app_name = "analytics"

urlpatterns = [
    # Workspace analytics
    path(
        "workspace/<int:workspace_id>/metrics/",
        WorkspaceAnalyticsView().get,
        name="workspace-metrics",
    ),

    # Project analytics
    path(
        "project/<int:project_id>/metrics/",
        ProjectAnalyticsView().get,
        name="project-metrics",
    ),

    # Team productivity
    path(
        "workspace/<int:workspace_id>/team-productivity/",
        TeamProductivityView().get,
        name="team-productivity",
    ),

    # Charts
    path(
        "project/<int:project_id>/burndown/",
        BurndownChartView().get,
        name="burndown-chart",
    ),
    path(
        "team/<str:team_id>/velocity/",
        VelocityChartView().get,
        name="velocity-chart",
    ),

    # Reports
    path(
        "reports/time_tracking/",
        TimeTrackingReportView().get,
        name="time-tracking-report",
    ),
]
