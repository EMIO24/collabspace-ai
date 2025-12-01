"""
CollabSpace AI - Analytics Services
Business logic for calculating analytics and metrics across the platform.
"""

from django.db.models import Count, Sum, Avg, Q, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from apps.workspaces.models import Workspace, WorkspaceMember
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task, TimeEntry
from apps.authentication.models import User


class WorkspaceAnalyticsService:
    """Service for workspace-level analytics and metrics."""
    
    @staticmethod
    def calculate_metrics(workspace_id: str) -> Dict:
        """
        Calculate comprehensive workspace metrics.
        
        Args:
            workspace_id: UUID of the workspace
            
        Returns:
            Dictionary containing all workspace metrics
        """
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return {'error': 'Workspace not found'}
        
        # Basic counts - WorkspaceMember uses is_active field
        total_members = WorkspaceMember.objects.filter(
            workspace=workspace,
            is_active=True
        ).count()
        
        # Project uses is_deleted field
        total_projects = Project.objects.filter(
            workspace=workspace,
            is_deleted=False
        ).count()
        
        # Task uses is_active field
        total_tasks = Task.objects.filter(
            project__workspace=workspace,
            is_active=True
        ).count()
        
        # Task breakdown
        completed_tasks = Task.objects.filter(
            project__workspace=workspace,
            is_active=True,
            status='done'
        ).count()
        
        pending_tasks = Task.objects.filter(
            project__workspace=workspace,
            is_active=True,
            status__in=['todo', 'in_progress', 'review']
        ).count()
        
        # Task completion rate
        completion_rate = (
            (completed_tasks / total_tasks * 100) 
            if total_tasks > 0 else 0
        )
        
        # Average completion time (in days)
        # Using updated_at as proxy for completion time since completed_at is in metadata
        completed_tasks_with_time = Task.objects.filter(
            project__workspace=workspace,
            is_active=True,
            status='done',
            created_at__isnull=False
        )
        
        avg_completion_time = 0
        if completed_tasks_with_time.exists():
            total_time = sum([
                (task.updated_at - task.created_at).total_seconds() / 86400
                for task in completed_tasks_with_time
            ])
            avg_completion_time = total_time / completed_tasks_with_time.count()
        
        # Member activity levels (tasks created or completed in last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_members = User.objects.filter(
            Q(created_tasks__project__workspace=workspace, 
              created_tasks__created_at__gte=thirty_days_ago,
              created_tasks__is_active=True) |
            Q(assigned_tasks__project__workspace=workspace,
              assigned_tasks__status='done',
              assigned_tasks__updated_at__gte=thirty_days_ago,
              assigned_tasks__is_active=True)
        ).distinct().count()
        
        # Activity rate
        activity_rate = (
            (active_members / total_members * 100)
            if total_members > 0 else 0
        )
        
        # Status distribution
        status_distribution = Task.objects.filter(
            project__workspace=workspace,
            is_active=True
        ).values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Priority distribution
        priority_distribution = Task.objects.filter(
            project__workspace=workspace,
            is_active=True
        ).values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        # Time tracking summary
        time_stats = TimeEntry.objects.filter(
            task__project__workspace=workspace,
            task__is_active=True
        ).aggregate(
            total_hours=Sum('hours'),
            avg_hours=Avg('hours')
        )
        
        return {
            'workspace_id': str(workspace_id),
            'workspace_name': workspace.name,
            'overview': {
                'total_members': total_members,
                'active_members': active_members,
                'activity_rate': round(activity_rate, 2),
                'total_projects': total_projects,
                'total_tasks': total_tasks,
            },
            'tasks': {
                'completed': completed_tasks,
                'pending': pending_tasks,
                'completion_rate': round(completion_rate, 2),
                'avg_completion_time_days': round(avg_completion_time, 2),
            },
            'distributions': {
                'by_status': list(status_distribution),
                'by_priority': list(priority_distribution),
            },
            'time_tracking': {
                'total_hours': float(time_stats['total_hours'] or 0),
                'avg_hours_per_entry': float(time_stats['avg_hours'] or 0),
            },
            'generated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def get_member_activity(workspace_id: str, days: int = 30) -> List[Dict]:
        """
        Get activity breakdown per member.
        
        Args:
            workspace_id: UUID of the workspace
            days: Number of days to look back
            
        Returns:
            List of member activity data
        """
        start_date = timezone.now() - timedelta(days=days)
        
        members = WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            is_active=True
        ).select_related('user')
        
        activity_data = []
        
        for member in members:
            tasks_created = Task.objects.filter(
                project__workspace_id=workspace_id,
                created_by=member.user,
                created_at__gte=start_date,
                is_active=True
            ).count()
            
            tasks_completed = Task.objects.filter(
                project__workspace_id=workspace_id,
                assigned_to=member.user,
                status='done',
                updated_at__gte=start_date,
                is_active=True
            ).count()
            
            hours_logged = TimeEntry.objects.filter(
                task__project__workspace_id=workspace_id,
                user=member.user,
                date__gte=start_date.date(),
                task__is_active=True
            ).aggregate(total=Sum('hours'))['total'] or 0
            
            activity_data.append({
                'user_id': str(member.user.id),
                'username': member.user.username,
                'full_name': member.user.get_full_name(),
                'tasks_created': tasks_created,
                'tasks_completed': tasks_completed,
                'hours_logged': float(hours_logged),
                'role': member.role,
            })
        
        # Sort by total activity
        activity_data.sort(
            key=lambda x: x['tasks_created'] + x['tasks_completed'] + x['hours_logged'],
            reverse=True
        )
        
        return activity_data


class ProjectAnalyticsService:
    """Service for project-level analytics and metrics."""
    
    @staticmethod
    def calculate_progress(project_id: str) -> Dict:
        """
        Calculate project progress metrics.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Dictionary containing project progress data
        """
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {'error': 'Project not found'}
        
        total_tasks = Task.objects.filter(
            project=project,
            is_active=True
        ).count()
        
        tasks_by_status = Task.objects.filter(
            project=project,
            is_active=True
        ).values('status').annotate(count=Count('id'))
        
        status_counts = {item['status']: item['count'] for item in tasks_by_status}
        
        completed = status_counts.get('done', 0)
        in_progress = status_counts.get('in_progress', 0)
        todo = status_counts.get('todo', 0)
        review = status_counts.get('review', 0)
        
        completion_percentage = (
            (completed / total_tasks * 100) if total_tasks > 0 else 0
        )
        
        # Estimated vs actual hours
        estimated_hours = Task.objects.filter(
            project=project,
            is_active=True
        ).aggregate(total=Sum('estimated_hours'))['total'] or 0
        
        actual_hours = TimeEntry.objects.filter(
            task__project=project,
            task__is_active=True
        ).aggregate(total=Sum('hours'))['total'] or 0
        
        # Overdue tasks
        overdue_tasks = Task.objects.filter(
            project=project,
            is_active=True,
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress', 'review']
        ).count()
        
        # Team members - ProjectMember doesn't have is_active, just count all
        team_size = ProjectMember.objects.filter(
            project=project
        ).count()
        
        return {
            'project_id': str(project_id),
            'project_name': project.name,
            'progress': {
                'total_tasks': total_tasks,
                'completed': completed,
                'in_progress': in_progress,
                'todo': todo,
                'review': review,
                'completion_percentage': round(completion_percentage, 2),
            },
            'time': {
                'estimated_hours': float(estimated_hours),
                'actual_hours': float(actual_hours),
                'variance': float(actual_hours - estimated_hours),
                'variance_percentage': round(
                    ((actual_hours - estimated_hours) / estimated_hours * 100)
                    if estimated_hours > 0 else 0,
                    2
                ),
            },
            'health': {
                'overdue_tasks': overdue_tasks,
                'team_size': team_size,
                'on_track': overdue_tasks == 0 and completion_percentage >= 50,
            },
            'generated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def generate_burndown_chart(
        project_id: str,
        sprint_start: datetime,
        sprint_end: datetime
    ) -> Dict:
        """
        Generate burndown chart data for a sprint.
        
        Args:
            project_id: UUID of the project
            sprint_start: Start date of the sprint
            sprint_end: End date of the sprint
            
        Returns:
            Dictionary containing burndown chart data
        """
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {'error': 'Project not found'}
        
        # Get total tasks at sprint start
        total_tasks = Task.objects.filter(
            project=project,
            created_at__lte=sprint_start,
            is_active=True
        ).count()
        
        # Calculate ideal burndown (linear)
        sprint_days = (sprint_end - sprint_start).days
        ideal_line = []
        
        for day in range(sprint_days + 1):
            remaining = total_tasks - (total_tasks * day / sprint_days)
            ideal_line.append({
                'day': day,
                'remaining': round(remaining, 2)
            })
        
        # Calculate actual burndown
        actual_line = []
        current_date = sprint_start
        
        while current_date <= sprint_end and current_date <= timezone.now():
            completed_by_date = Task.objects.filter(
                project=project,
                status='done',
                updated_at__lte=current_date,
                created_at__lte=sprint_start,
                is_active=True
            ).count()
            
            remaining = total_tasks - completed_by_date
            day_number = (current_date - sprint_start).days
            
            actual_line.append({
                'day': day_number,
                'date': current_date.date().isoformat(),
                'remaining': remaining,
                'completed': completed_by_date
            })
            
            current_date += timedelta(days=1)
        
        return {
            'project_id': str(project_id),
            'project_name': project.name,
            'sprint': {
                'start': sprint_start.isoformat(),
                'end': sprint_end.isoformat(),
                'total_days': sprint_days,
                'total_tasks': total_tasks,
            },
            'ideal_burndown': ideal_line,
            'actual_burndown': actual_line,
            'generated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def calculate_velocity(project_id: str, num_sprints: int = 5) -> Dict:
        """
        Calculate team velocity over the last N sprints.
        
        Note: This assumes sprints are 2-week periods. You may want to
        store actual sprint data in a Sprint model for more accuracy.
        
        Args:
            project_id: UUID of the project
            num_sprints: Number of sprints to analyze
            
        Returns:
            Dictionary containing velocity data
        """
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return {'error': 'Project not found'}
        
        sprint_length_days = 14  # 2-week sprints
        velocity_data = []
        
        for sprint_num in range(num_sprints):
            sprint_end = timezone.now() - timedelta(days=sprint_num * sprint_length_days)
            sprint_start = sprint_end - timedelta(days=sprint_length_days)
            
            # Tasks completed in this sprint
            completed_tasks = Task.objects.filter(
                project=project,
                status='done',
                updated_at__gte=sprint_start,
                updated_at__lt=sprint_end,
                is_active=True
            ).count()
            
            # Story points (if you have them, otherwise use task count)
            # Assuming estimated_hours can serve as story points proxy
            story_points = Task.objects.filter(
                project=project,
                status='done',
                updated_at__gte=sprint_start,
                updated_at__lt=sprint_end,
                is_active=True
            ).aggregate(
                points=Sum('estimated_hours')
            )['points'] or 0
            
            velocity_data.append({
                'sprint_number': num_sprints - sprint_num,
                'sprint_start': sprint_start.date().isoformat(),
                'sprint_end': sprint_end.date().isoformat(),
                'tasks_completed': completed_tasks,
                'story_points': float(story_points),
            })
        
        # Reverse to show oldest to newest
        velocity_data.reverse()
        
        # Calculate average velocity
        avg_tasks = sum(s['tasks_completed'] for s in velocity_data) / num_sprints
        avg_points = sum(s['story_points'] for s in velocity_data) / num_sprints
        
        return {
            'project_id': str(project_id),
            'project_name': project.name,
            'sprints_analyzed': num_sprints,
            'velocity_per_sprint': velocity_data,
            'average_velocity': {
                'tasks': round(avg_tasks, 2),
                'story_points': round(avg_points, 2),
            },
            'generated_at': timezone.now().isoformat()
        }


class TeamProductivityService:
    """Service for team and individual productivity metrics."""
    
    @staticmethod
    def calculate_productivity_score(
        user_id: str,
        date_range: Tuple[datetime, datetime]
    ) -> Dict:
        """
        Calculate productivity metrics for a user.
        
        Args:
            user_id: UUID of the user
            date_range: Tuple of (start_date, end_date)
            
        Returns:
            Dictionary containing productivity metrics
        """
        start_date, end_date = date_range
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return {'error': 'User not found'}
        
        # Tasks completed
        tasks_completed = Task.objects.filter(
            assigned_to=user,
            status='done',
            updated_at__gte=start_date,
            updated_at__lte=end_date,
            is_active=True
        ).count()
        
        # Tasks created
        tasks_created = Task.objects.filter(
            created_by=user,
            created_at__gte=start_date,
            created_at__lte=end_date,
            is_active=True
        ).count()
        
        # Hours logged
        hours_logged = TimeEntry.objects.filter(
            user=user,
            date__gte=start_date.date(),
            date__lte=end_date.date()
        ).aggregate(total=Sum('hours'))['total'] or 0
        
        # Average completion time
        completed_tasks = Task.objects.filter(
            assigned_to=user,
            status='done',
            updated_at__gte=start_date,
            updated_at__lte=end_date,
            created_at__isnull=False,
            is_active=True
        )
        
        avg_completion_time = 0
        if completed_tasks.exists():
            total_time = sum([
                (task.updated_at - task.created_at).total_seconds() / 3600
                for task in completed_tasks
            ])
            avg_completion_time = total_time / completed_tasks.count()
        
        # On-time delivery rate
        on_time_tasks = Task.objects.filter(
            assigned_to=user,
            status='done',
            updated_at__gte=start_date,
            updated_at__lte=end_date,
            due_date__isnull=False,
            is_active=True
        ).annotate(
            on_time=ExpressionWrapper(
                Q(updated_at__lte=F('due_date')),
                output_field=FloatField()
            )
        )
        
        on_time_count = sum(1 for task in on_time_tasks if task.updated_at <= task.due_date)
        on_time_rate = (
            (on_time_count / on_time_tasks.count() * 100)
            if on_time_tasks.count() > 0 else 0
        )
        
        # Calculate productivity score (0-100)
        # Weighted formula: 40% completion + 20% on-time + 20% hours + 20% created
        days_in_range = (end_date - start_date).days + 1
        
        completion_score = min((tasks_completed / days_in_range) * 10, 40)
        on_time_score = (on_time_rate / 100) * 20
        hours_score = min((float(hours_logged) / days_in_range) * 2.5, 20)
        creation_score = min((tasks_created / days_in_range) * 5, 20)
        
        productivity_score = completion_score + on_time_score + hours_score + creation_score
        
        return {
            'user_id': str(user_id),
            'username': user.username,
            'full_name': user.get_full_name(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days_in_range,
            },
            'metrics': {
                'tasks_completed': tasks_completed,
                'tasks_created': tasks_created,
                'hours_logged': float(hours_logged),
                'avg_completion_time_hours': round(avg_completion_time, 2),
                'on_time_delivery_rate': round(on_time_rate, 2),
            },
            'productivity_score': round(productivity_score, 2),
            'score_breakdown': {
                'completion': round(completion_score, 2),
                'on_time': round(on_time_score, 2),
                'hours': round(hours_score, 2),
                'creation': round(creation_score, 2),
            },
            'generated_at': timezone.now().isoformat()
        }
    
    @staticmethod
    def identify_top_performers(
        workspace_id: str,
        period: str = 'month'
    ) -> List[Dict]:
        """
        Identify top contributors in a workspace.
        
        Args:
            workspace_id: UUID of the workspace
            period: Time period ('week', 'month', 'quarter', 'year')
            
        Returns:
            List of top performers with their metrics
        """
        # Calculate date range based on period
        now = timezone.now()
        period_map = {
            'week': timedelta(days=7),
            'month': timedelta(days=30),
            'quarter': timedelta(days=90),
            'year': timedelta(days=365),
        }
        
        start_date = now - period_map.get(period, timedelta(days=30))
        
        # Get all active members
        members = WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            is_active=True
        ).select_related('user')
        
        performers = []
        
        for member in members:
            score_data = TeamProductivityService.calculate_productivity_score(
                user_id=str(member.user.id),
                date_range=(start_date, now)
            )
            
            if 'error' not in score_data:
                performers.append(score_data)
        
        # Sort by productivity score
        performers.sort(key=lambda x: x['productivity_score'], reverse=True)
        
        # Add ranking
        for idx, performer in enumerate(performers, 1):
            performer['rank'] = idx
        
        return performers[:10]  # Return top 10