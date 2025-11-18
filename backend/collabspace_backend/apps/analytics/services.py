import csv
from datetime import datetime, timedelta
from io import StringIO
from collections import defaultdict
from typing import Dict, List, Any

# Assuming these imports from our mock models
from .models import CachedReport, MockTask, MockTimeEntry, MockProject

class AnalyticsService:
    """
    Central service layer for all analytics calculations, charting, and data export.
    """

    @staticmethod
    def _fetch_mock_tasks(project_id=None, workspace_id=None) -> List[MockTask]:
        """Simulates fetching tasks from the database."""
        base_date = datetime.now() - timedelta(days=30)
        tasks = [
            MockTask(1, 'Done', 'M', 101, 'user_A', base_date + timedelta(days=2)),
            MockTask(2, 'Done', 'L', 101, 'user_A', base_date + timedelta(days=5)),
            MockTask(3, 'In Progress', 'S', 101, 'user_B', base_date + timedelta(days=10)),
            MockTask(4, 'To Do', 'M', 102, 'user_A', base_date + timedelta(days=15)),
            MockTask(5, 'Done', 'S', 102, 'user_C', base_date + timedelta(days=20)),
            MockTask(6, 'Done', 'M', 101, 'user_B', base_date + timedelta(days=25)),
            MockTask(7, 'In Progress', 'L', 102, 'user_C', base_date + timedelta(days=28)),
        ]
        if project_id:
            return [t for t in tasks if t.project_id == project_id]
        # In a real scenario, this would filter by workspace_id
        return tasks

    @staticmethod
    def _fetch_mock_time_entries(task_ids: List[int]) -> List[MockTimeEntry]:
        """Simulates fetching time entries."""
        if not task_ids:
            return []
        return [
            MockTimeEntry('user_A', 1, 4.5, datetime.now().date() - timedelta(days=10)),
            MockTimeEntry('user_A', 2, 8.0, datetime.now().date() - timedelta(days=9)),
            MockTimeEntry('user_B', 6, 3.0, datetime.now().date() - timedelta(days=5)),
            MockTimeEntry('user_C', 5, 2.0, datetime.now().date() - timedelta(days=1)),
        ]

    @staticmethod
    def _fetch_mock_projects(workspace_id: int) -> List[MockProject]:
        """Simulates fetching projects."""
        if workspace_id == 1:
            return [
                MockProject(101, 'Frontend Redesign', datetime.now() - timedelta(days=60), datetime.now() + timedelta(days=30)),
                MockProject(102, 'API Optimization', datetime.now() - timedelta(days=45), datetime.now() + timedelta(days=45)),
            ]
        return []

    def calculate_workspace_metrics(self, workspace_id: int) -> Dict[str, Any]:
        """
        Calculates high-level metrics for an entire workspace.
        Implements basic caching logic.
        """
        cache_key = f'workspace_{workspace_id}_metrics_cache'
        cached_data = CachedReport.find_latest(cache_key)
        if cached_data:
            return cached_data.data

        # --- Calculation Logic (Cache Miss) ---
        tasks = self._fetch_mock_tasks(workspace_id=workspace_id)
        projects = self._fetch_mock_projects(workspace_id)

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'Done'])
        in_progress_tasks = total_tasks - completed_tasks - len([t for t in tasks if t.status == 'To Do'])

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks else 0

        metrics = {
            'workspace_id': workspace_id,
            'total_projects': len(projects),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completion_rate_percent': round(completion_rate, 2),
            'average_task_cycle_days': 7.5, # Mock calculation
        }

        # --- Cache the result ---
        report = CachedReport(report_key=cache_key, data=metrics)
        report.save()

        return metrics

    def calculate_project_metrics(self, project_id: int) -> Dict[str, Any]:
        """
        Calculates detailed performance metrics for a specific project.
        """
        tasks = self._fetch_mock_tasks(project_id=project_id)
        project_tasks_ids = [t.id for t in tasks]
        time_entries = self._fetch_mock_time_entries(project_tasks_ids)

        # Effort Mapping (M, S, L to points)
        effort_map = {'S': 1, 'M': 3, 'L': 5}
        total_story_points = sum(effort_map.get(t.complexity, 0) for t in tasks)
        completed_points = sum(effort_map.get(t.complexity, 0) for t in tasks if t.status == 'Done')
        
        total_logged_hours = sum(e.hours for e in time_entries)

        metrics = {
            'project_id': project_id,
            'total_tasks': len(tasks),
            'completed_tasks': len([t for t in tasks if t.status == 'Done']),
            'total_story_points': total_story_points,
            'completed_story_points': completed_points,
            'burn_rate_hours': round(total_logged_hours, 1),
            'points_completion_percent': round((completed_points / total_story_points * 100) if total_story_points else 0, 2),
        }
        return metrics

    def calculate_team_productivity(self, workspace_id: int) -> List[Dict[str, Any]]:
        """
        Calculates productivity metrics per team member.
        """
        tasks = self._fetch_mock_tasks(workspace_id=workspace_id)
        task_ids = [t.id for t in tasks]
        time_entries = self._fetch_mock_time_entries(task_ids)

        user_metrics = defaultdict(lambda: {'tasks_completed': 0, 'points_completed': 0, 'logged_hours': 0})
        effort_map = {'S': 1, 'M': 3, 'L': 5}
        
        # 1. Aggregate task completion
        for task in tasks:
            if task.status == 'Done':
                user_metrics[task.assigned_to]['tasks_completed'] += 1
                user_metrics[task.assigned_to]['points_completed'] += effort_map.get(task.complexity, 0)

        # 2. Aggregate time logging
        for entry in time_entries:
            user_metrics[entry.user_id]['logged_hours'] += entry.hours

        # 3. Format output
        results = []
        for user_id, data in user_metrics.items():
            results.append({
                'user_id': user_id,
                'tasks_completed': data['tasks_completed'],
                'points_completed': data['points_completed'],
                'logged_hours': round(data['logged_hours'], 1),
                'points_per_hour': round(data['points_completed'] / data['logged_hours'], 2) if data['logged_hours'] else 0
            })

        return results

    def generate_burndown_chart(self, project_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Generates data points for a burndown chart (remaining effort vs time).
        """
        tasks = self._fetch_mock_tasks(project_id=project_id)
        effort_map = {'S': 1, 'M': 3, 'L': 5}
        initial_effort = sum(effort_map.get(t.complexity, 0) for t in tasks)
        
        # Mocking the burndown curve
        burndown_data = []
        current_date = datetime.now().date() - timedelta(days=days)
        remaining_effort = initial_effort
        
        for i in range(days + 1):
            date_str = (current_date + timedelta(days=i)).isoformat()
            
            # Simulate a drop in effort (points completed)
            if i % 5 == 0 and i > 0:
                points_completed = 3
                remaining_effort = max(0, remaining_effort - points_completed)
            
            burndown_data.append({
                'date': date_str,
                'remaining_points': remaining_effort,
                'ideal_points': initial_effort - (initial_effort / days) * i
            })
            
        return {
            'project_id': project_id,
            'chart_title': f"Burndown Chart for P-{project_id}",
            'initial_effort': initial_effort,
            'data_points': burndown_data
        }

    def generate_velocity_chart(self, team_id: str, sprints: int = 5) -> Dict[str, Any]:
        """
        Generates data for a velocity chart (completed effort per sprint).
        """
        # Mocking sprint data
        velocity_data = []
        for i in range(sprints):
            velocity_data.append({
                'sprint_name': f'Sprint {i+1}',
                'committed_points': 30 + (i * 2), # increasing commitment
                'completed_points': 25 + (i * 3) % 7, # slightly variable completion
            })
            
        # Calculate average velocity
        total_completed = sum(d['completed_points'] for d in velocity_data)
        average_velocity = round(total_completed / sprints, 2) if sprints else 0

        return {
            'team_id': team_id,
            'chart_title': f"Velocity Chart for Team {team_id}",
            'average_velocity': average_velocity,
            'data_points': velocity_data
        }

    def generate_time_tracking_report_csv(self, user_id: str, start_date: datetime, end_date: datetime) -> str:
        """
        Generates a detailed time tracking report as a CSV string.
        """
        # Mock data (in a real app, this would query TimeEntry for the user/date range)
        mock_entries = self._fetch_mock_time_entries([1, 2, 5, 6])
        user_entries = [e for e in mock_entries if e.user_id == user_id]

        output = StringIO()
        writer = csv.writer(output)

        # CSV Header
        writer.writerow(['Date', 'User ID', 'Task ID', 'Hours Logged', 'Description (Mock)'])

        # CSV Data Rows
        for entry in user_entries:
            # Check date range (mocking the query filter)
            if start_date.date() <= entry.date <= end_date.date():
                writer.writerow([
                    entry.date.isoformat(),
                    entry.user_id,
                    entry.task_id,
                    entry.hours,
                    f"Work on task {entry.task_id}"
                ])

        return output.getvalue()