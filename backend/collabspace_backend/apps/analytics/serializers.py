# Note: In a real Django Rest Framework project, this would import from rest_framework import serializers

class MockSerializer:
    """Mock base class for DRF Serializer functionality."""
    def __init__(self, data=None):
        self.data = data

    def to_representation(self, instance):
        return instance

    @property
    def is_valid(self):
        return True # Mocking validation success

    @property
    def errors(self):
        return {} # Mocking no errors

class WorkspaceAnalyticsSerializer(MockSerializer):
    """Serializer for Workspace-level aggregated metrics."""
    def to_representation(self, instance):
        return {
            'workspace_id': instance.get('workspace_id'),
            'total_projects': instance.get('total_projects'),
            'total_tasks': instance.get('total_tasks'),
            'completed_tasks': instance.get('completed_tasks'),
            'in_progress_tasks': instance.get('in_progress_tasks'),
            'completion_rate_percent': f"{instance.get('completion_rate_percent', 0)}%",
            'average_task_cycle_days': instance.get('average_task_cycle_days'),
            # Include a cache status flag if desired
            'cache_hit': instance.get('cache_hit', False)
        }

class ProjectAnalyticsSerializer(MockSerializer):
    """Serializer for Project-level metrics."""
    def to_representation(self, instance):
        return {
            'project_id': instance.get('project_id'),
            'total_tasks': instance.get('total_tasks'),
            'completed_tasks': instance.get('completed_tasks'),
            'total_story_points': instance.get('total_story_points'),
            'completed_story_points': instance.get('completed_story_points'),
            'burn_rate_hours': instance.get('burn_rate_hours'),
            'points_completion_percent': f"{instance.get('points_completion_percent', 0)}%",
        }

class TeamProductivitySerializer(MockSerializer):
    """Serializer for individual team member productivity."""
    def to_representation(self, instance):
        return {
            'user_id': instance.get('user_id'),
            'tasks_completed': instance.get('tasks_completed'),
            'points_completed': instance.get('points_completed'),
            'logged_hours': instance.get('logged_hours'),
            'points_per_hour': instance.get('points_per_hour'),
        }

# Serializers for Chart Data (simply pass through the structured data)
class BurndownChartSerializer(MockSerializer):
    pass

class VelocityChartSerializer(MockSerializer):
    pass