"""
Project URL configuration for CollabSpace AI.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, ProjectMemberViewSet, ProjectLabelViewSet,
    ProjectStatsView, ProjectActivityView
)

app_name = 'projects'

router = DefaultRouter()
router.register('', ProjectViewSet, basename='project')

urlpatterns = [
    # Main project routes
    path('', include(router.urls)),
    
    # Project stats
    path('<uuid:id>/stats/', ProjectStatsView.as_view(), name='project-stats'),
    
    # Project activity
    path('<uuid:id>/activity/', ProjectActivityView.as_view(), name='project-activity'),
    
    # Project members
    path('<uuid:project_id>/members/', ProjectMemberViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='project-members'),
    path('<uuid:project_id>/members/<uuid:user_id>/', ProjectMemberViewSet.as_view({
        'delete': 'destroy'
    }), name='project-member-detail'),
    
    # Project labels
    path('<uuid:project_id>/labels/', ProjectLabelViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='project-labels'),
    path('<uuid:project_id>/labels/<int:pk>/', ProjectLabelViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    }), name='project-label-detail'),
]