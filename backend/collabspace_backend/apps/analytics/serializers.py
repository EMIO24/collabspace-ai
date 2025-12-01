"""
CollabSpace AI - Analytics Serializers
Serializers for analytics data validation and output formatting.
"""

from rest_framework import serializers
from datetime import datetime, timedelta
from django.utils import timezone


class WorkspaceAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for workspace analytics query parameters."""
    workspace_id = serializers.UUIDField(required=True)


class ProjectAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for project analytics query parameters."""
    project_id = serializers.UUIDField(required=True)


class BurndownChartQuerySerializer(serializers.Serializer):
    """Serializer for burndown chart query parameters."""
    project_id = serializers.UUIDField(required=True)
    sprint_start = serializers.DateTimeField(required=True)
    sprint_end = serializers.DateTimeField(required=True)
    
    def validate(self, data):
        """Validate that sprint_end is after sprint_start."""
        if data['sprint_end'] <= data['sprint_start']:
            raise serializers.ValidationError(
                "sprint_end must be after sprint_start"
            )
        return data


class VelocityQuerySerializer(serializers.Serializer):
    """Serializer for velocity chart query parameters."""
    project_id = serializers.UUIDField(required=True)
    num_sprints = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20
    )


class TeamProductivityQuerySerializer(serializers.Serializer):
    """Serializer for team productivity query parameters."""
    workspace_id = serializers.UUIDField(required=True)
    user_id = serializers.UUIDField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    period = serializers.ChoiceField(
        choices=['week', 'month', 'quarter', 'year'],
        required=False,
        default='month'
    )
    
    def validate(self, data):
        """Set default date range if not provided."""
        if not data.get('start_date') or not data.get('end_date'):
            period_map = {
                'week': timedelta(days=7),
                'month': timedelta(days=30),
                'quarter': timedelta(days=90),
                'year': timedelta(days=365),
            }
            data['end_date'] = timezone.now()
            data['start_date'] = data['end_date'] - period_map[data['period']]
        
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                "end_date must be after start_date"
            )
        
        return data


class TimeTrackingReportQuerySerializer(serializers.Serializer):
    """Serializer for time tracking report query parameters."""
    workspace_id = serializers.UUIDField(required=False)
    project_id = serializers.UUIDField(required=False)
    user_id = serializers.UUIDField(required=False)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    group_by = serializers.ChoiceField(
        choices=['date', 'user', 'project', 'task'],
        required=False,
        default='date'
    )
    export_format = serializers.ChoiceField(
        choices=['json', 'csv', 'pdf'],
        required=False,
        default='json'
    )
    
    def validate(self, data):
        """Validate that at least one filter is provided."""
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                "end_date must be after start_date"
            )
        
        if not any([
            data.get('workspace_id'),
            data.get('project_id'),
            data.get('user_id')
        ]):
            raise serializers.ValidationError(
                "At least one of workspace_id, project_id, or user_id is required"
            )
        
        return data


class MemberActivityQuerySerializer(serializers.Serializer):
    """Serializer for member activity query parameters."""
    workspace_id = serializers.UUIDField(required=True)
    days = serializers.IntegerField(
        required=False,
        default=30,
        min_value=1,
        max_value=365
    )


class TopPerformersQuerySerializer(serializers.Serializer):
    """Serializer for top performers query parameters."""
    workspace_id = serializers.UUIDField(required=True)
    period = serializers.ChoiceField(
        choices=['week', 'month', 'quarter', 'year'],
        required=False,
        default='month'
    )
    limit = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=50
    )


# Output Serializers

class OverviewMetricsSerializer(serializers.Serializer):
    """Serializer for overview metrics."""
    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    activity_rate = serializers.FloatField()
    total_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()


class TaskMetricsSerializer(serializers.Serializer):
    """Serializer for task metrics."""
    completed = serializers.IntegerField()
    pending = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_completion_time_days = serializers.FloatField()


class DistributionItemSerializer(serializers.Serializer):
    """Serializer for distribution item."""
    status = serializers.CharField(required=False)
    priority = serializers.CharField(required=False)
    count = serializers.IntegerField()


class DistributionsSerializer(serializers.Serializer):
    """Serializer for distributions."""
    by_status = DistributionItemSerializer(many=True)
    by_priority = DistributionItemSerializer(many=True)


class TimeTrackingStatsSerializer(serializers.Serializer):
    """Serializer for time tracking statistics."""
    total_hours = serializers.FloatField()
    avg_hours_per_entry = serializers.FloatField()


class WorkspaceMetricsOutputSerializer(serializers.Serializer):
    """Output serializer for workspace metrics."""
    workspace_id = serializers.UUIDField()
    workspace_name = serializers.CharField()
    overview = OverviewMetricsSerializer()
    tasks = TaskMetricsSerializer()
    distributions = DistributionsSerializer()
    time_tracking = TimeTrackingStatsSerializer()
    generated_at = serializers.DateTimeField()


class MemberActivitySerializer(serializers.Serializer):
    """Serializer for member activity data."""
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    tasks_created = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()
    hours_logged = serializers.FloatField()
    role = serializers.CharField()


class ProgressMetricsSerializer(serializers.Serializer):
    """Serializer for progress metrics."""
    total_tasks = serializers.IntegerField()
    completed = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    todo = serializers.IntegerField()
    review = serializers.IntegerField()
    completion_percentage = serializers.FloatField()


class TimeVarianceSerializer(serializers.Serializer):
    """Serializer for time variance metrics."""
    estimated_hours = serializers.FloatField()
    actual_hours = serializers.FloatField()
    variance = serializers.FloatField()
    variance_percentage = serializers.FloatField()


class ProjectHealthSerializer(serializers.Serializer):
    """Serializer for project health metrics."""
    overdue_tasks = serializers.IntegerField()
    team_size = serializers.IntegerField()
    on_track = serializers.BooleanField()


class ProjectProgressOutputSerializer(serializers.Serializer):
    """Output serializer for project progress."""
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    progress = ProgressMetricsSerializer()
    time = TimeVarianceSerializer()
    health = ProjectHealthSerializer()
    generated_at = serializers.DateTimeField()


class BurndownPointSerializer(serializers.Serializer):
    """Serializer for a single burndown chart point."""
    day = serializers.IntegerField()
    remaining = serializers.FloatField()
    date = serializers.DateField(required=False)
    completed = serializers.IntegerField(required=False)


class SprintInfoSerializer(serializers.Serializer):
    """Serializer for sprint information."""
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    total_days = serializers.IntegerField()
    total_tasks = serializers.IntegerField()


class BurndownChartOutputSerializer(serializers.Serializer):
    """Output serializer for burndown chart."""
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    sprint = SprintInfoSerializer()
    ideal_burndown = BurndownPointSerializer(many=True)
    actual_burndown = BurndownPointSerializer(many=True)
    generated_at = serializers.DateTimeField()


class VelocitySprintSerializer(serializers.Serializer):
    """Serializer for velocity sprint data."""
    sprint_number = serializers.IntegerField()
    sprint_start = serializers.DateField()
    sprint_end = serializers.DateField()
    tasks_completed = serializers.IntegerField()
    story_points = serializers.FloatField()


class AverageVelocitySerializer(serializers.Serializer):
    """Serializer for average velocity."""
    tasks = serializers.FloatField()
    story_points = serializers.FloatField()


class VelocityOutputSerializer(serializers.Serializer):
    """Output serializer for velocity data."""
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    sprints_analyzed = serializers.IntegerField()
    velocity_per_sprint = VelocitySprintSerializer(many=True)
    average_velocity = AverageVelocitySerializer()
    generated_at = serializers.DateTimeField()


class PeriodInfoSerializer(serializers.Serializer):
    """Serializer for time period information."""
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    days = serializers.IntegerField()


class ProductivityMetricsSerializer(serializers.Serializer):
    """Serializer for productivity metrics."""
    tasks_completed = serializers.IntegerField()
    tasks_created = serializers.IntegerField()
    hours_logged = serializers.FloatField()
    avg_completion_time_hours = serializers.FloatField()
    on_time_delivery_rate = serializers.FloatField()


class ScoreBreakdownSerializer(serializers.Serializer):
    """Serializer for productivity score breakdown."""
    completion = serializers.FloatField()
    on_time = serializers.FloatField()
    hours = serializers.FloatField()
    creation = serializers.FloatField()


class ProductivityOutputSerializer(serializers.Serializer):
    """Output serializer for productivity data."""
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    period = PeriodInfoSerializer()
    metrics = ProductivityMetricsSerializer()
    productivity_score = serializers.FloatField()
    score_breakdown = ScoreBreakdownSerializer()
    rank = serializers.IntegerField(required=False)
    generated_at = serializers.DateTimeField()


class TimeEntryReportItemSerializer(serializers.Serializer):
    """Serializer for time entry report item."""
    date = serializers.DateField(required=False)
    user = serializers.CharField(required=False)
    project = serializers.CharField(required=False)
    task = serializers.CharField(required=False)
    hours = serializers.FloatField()
    description = serializers.CharField(required=False, allow_blank=True)


class TimeTrackingReportOutputSerializer(serializers.Serializer):
    """Output serializer for time tracking report."""
    period = serializers.DictField()
    filters = serializers.DictField()
    summary = serializers.DictField()
    entries = TimeEntryReportItemSerializer(many=True)
    grouped_data = serializers.ListField(required=False)
    generated_at = serializers.DateTimeField()