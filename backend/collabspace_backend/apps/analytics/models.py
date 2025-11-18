from datetime import datetime, timedelta

# Note: In a real Django project, this would import from django.db import models
# We will use a simple class structure for demonstration.

class CachedReport:
    """
    Mock model representing a cached analytics report result.
    In a real system, this would store complex JSON or serialized data.
    """
    def __init__(self, report_key, data, created_at=None, expires_at=None):
        self.report_key = report_key  # e.g., 'workspace_123_metrics'
        self.data = data             # The actual analytics data (e.g., JSON string or dict)
        self.created_at = created_at if created_at is not None else datetime.now()
        # Default cache expiry: 1 hour
        self.expires_at = expires_at if expires_at is not None else (self.created_at + timedelta(hours=1))

    @classmethod
    def find_latest(cls, report_key):
        """
        Mock ORM lookup for the latest non-expired report.
        In a real scenario, this would be a database query.
        """
        # Simulated in-memory cache for demonstration
        if report_key == 'workspace_1_metrics_cache' and datetime.now() < datetime.now() + timedelta(minutes=5):
            print(f"DEBUG: Serving cached data for {report_key}.")
            return cls(
                report_key=report_key,
                data={'total_projects': 5, 'completed_tasks': 150, 'cache_hit': True},
                expires_at=datetime.now() + timedelta(minutes=5)
            )
        print(f"DEBUG: Cache miss for {report_key}. Recalculating.")
        return None

    def save(self):
        """
        Mock ORM save operation.
        """
        print(f"DEBUG: Saving new cache entry for {self.report_key}.")
        # In a real app, this would save to the database.
        pass

# Mock for other core models needed in services.py
class MockTask:
    def __init__(self, id, status, complexity, project_id, assigned_to, created_at):
        self.id = id
        self.status = status # 'To Do', 'In Progress', 'Done'
        self.complexity = complexity # 'S', 'M', 'L' -> for story points/effort
        self.project_id = project_id
        self.assigned_to = assigned_to # User ID
        self.created_at = created_at

class MockTimeEntry:
    def __init__(self, user_id, task_id, hours, date):
        self.user_id = user_id
        self.task_id = task_id
        self.hours = hours
        self.date = date

class MockProject:
    def __init__(self, id, name, start_date, end_date):
        self.id = id
        self.name = name
        self.start_date = start_date
        self.end_date = end_date