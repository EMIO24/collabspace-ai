"""
CollabSpace AI - Analytics Module URLs
Routing configuration for all analytics-related API endpoints.
"""

from django.urls import path
from .views import (
    WorkspaceAnalyticsView,
    WorkspaceMemberActivityView,
    ProjectAnalyticsView,
    BurndownChartView,
    VelocityChartView,
    TeamProductivityView,
    TopPerformersView,
    TimeTrackingReportView,
    TeamVelocityView
)

app_name = 'analytics'

urlpatterns = [
    # Workspace Analytics
    path(
        'workspace/<uuid:workspace_id>/metrics/',
        WorkspaceAnalyticsView.as_view(),
        name='workspace-metrics'
    ),
    path(
        'workspace/<uuid:workspace_id>/member-activity/',
        WorkspaceMemberActivityView.as_view(),
        name='workspace-member-activity'
    ),
    path(
        'workspace/<uuid:workspace_id>/team-productivity/',
        TeamProductivityView.as_view(),
        name='workspace-team-productivity'
    ),
    path(
        'workspace/<uuid:workspace_id>/top-performers/',
        TopPerformersView.as_view(),
        name='workspace-top-performers'
    ),
    
    # Project Analytics
    path(
        'project/<uuid:project_id>/metrics/',
        ProjectAnalyticsView.as_view(),
        name='project-metrics'
    ),
    path(
        'project/<uuid:project_id>/burndown/',
        BurndownChartView.as_view(),
        name='project-burndown'
    ),
    path(
        'project/<uuid:project_id>/velocity/',
        VelocityChartView.as_view(),
        name='project-velocity'
    ),
    
    # Time Tracking Reports
    path(
        'reports/time-tracking/',
        TimeTrackingReportView.as_view(),
        name='time-tracking-report'
    ),

    path(
    'team/<slug:team_id>/velocity/',
    TeamVelocityView.as_view(), # You would need to create this view
    name='team-velocity'
    ),
]