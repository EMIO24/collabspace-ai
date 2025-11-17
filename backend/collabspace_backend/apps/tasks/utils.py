from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from apps.tasks.models import Task, TimeEntry

def auto_assign_task(task, project):
    """
    Automatically assign task based on workload and availability.
    
    Args:
        task: Task instance
        project: Project instance
    
    Returns:
        Assigned user or None
    """
    # Get project members
    members = project.members.all()
    
    if not members.exists():
        return None
    
    # Calculate workload for each member
    workload = {}
    for member in members:
        active_tasks = Task.objects.filter(
            assigned_to=member,
            status__in=['todo', 'in_progress', 'review'],
            is_active=True
        ).count()
        workload[member.id] = active_tasks
    
    # Assign to member with least workload
    if workload:
        least_loaded = min(workload, key=workload.get)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=least_loaded)
    
    return None

def suggest_due_date(task, project):
    """
    Suggest due date based on task priority and project schedule.
    
    Args:
        task: Task instance
        project: Project instance
    
    Returns:
        Suggested due date
    """
    now = timezone.now()
    
    priority_days = {
        'urgent': 1,
        'high': 3,
        'medium': 7,
        'low': 14
    }
    
    days = priority_days.get(task.priority, 7)
    
    # Check if task has estimated hours
    if task.estimated_hours:
        # Assume 6 working hours per day
        days = max(days, int(task.estimated_hours / 6) + 1)
    
    return now + timedelta(days=days)

def detect_task_bottlenecks(project):
    """
    Detect bottlenecks in task workflow.
    
    Args:
        project: Project instance
    
    Returns:
        Dict with bottleneck analysis
    """
    tasks = Task.objects.filter(project=project, is_active=True)
    
    bottlenecks = {
        'overdue': [],
        'blocked': [],
        'unassigned': [],
        'stalled': [],
        'over_budget': []
    }
    
    cutoff = timezone.now() - timedelta(days=7)
    
    for task in tasks:
        # Overdue tasks
        if task.due_date and task.due_date < timezone.now() and task.status != 'done':
            bottlenecks['overdue'].append({
                'id': task.id,
                'title': task.title,
                'due_date': task.due_date
            })
        
        # Blocked tasks (simplified - you'd need dependency logic)
        blocking_tasks = task.blocked_by.all()
        if blocking_tasks.exists():
            bottlenecks['blocked'].append({
                'id': task.id,
                'title': task.title,
                'blocking_tasks': [t.title for t in blocking_tasks]
            })
        
        # Unassigned tasks
        if not task.assigned_to:
            bottlenecks['unassigned'].append({
                'id': task.id,
                'title': task.title,
                'priority': task.priority
            })
        
        # Stalled tasks (not updated in 7 days)
        if task.updated_at < cutoff and task.status != 'done':
            bottlenecks['stalled'].append({
                'id': task.id,
                'title': task.title,
                'last_updated': task.updated_at
            })
        
        # Over budget
        if task.estimated_hours:
            actual_hours = TimeEntry.objects.filter(task=task).aggregate(
                total=Sum('hours')
            )['total'] or 0
            if actual_hours > task.estimated_hours:
                bottlenecks['over_budget'].append({
                    'id': task.id,
                    'title': task.title,
                    'estimated': float(task.estimated_hours),
                    'actual': float(actual_hours),
                    'overrun': float(actual_hours - task.estimated_hours)
                })
    
    return bottlenecks

def generate_task_report(project, start_date=None, end_date=None):
    """
    Generate comprehensive task report for a project.
    
    Args:
        project: Project instance
        start_date: Report start date
        end_date: Report end date
    
    Returns:
        Dict with report data
    """
    queryset = Task.objects.filter(project=project, is_active=True)
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    # Basic statistics
    total_tasks = queryset.count()
    completed_tasks = queryset.filter(status='done').count()
    
    # Status breakdown
    status_breakdown = queryset.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Priority breakdown
    priority_breakdown = queryset.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    # Time tracking
    total_estimated = queryset.aggregate(
        total=Sum('estimated_hours')
    )['total'] or 0
    
    total_actual = TimeEntry.objects.filter(
        task__in=queryset
    ).aggregate(total=Sum('hours'))['total'] or 0
    
    # Team performance
    team_stats = queryset.values(
        'assigned_to__username'
    ).annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='done')),
        in_progress=Count('id', filter=Q(status='in_progress'))
    ).order_by('-total')
    
    # Velocity (tasks completed per week)
    if start_date and end_date:
        weeks = (end_date - start_date).days / 7
        velocity = completed_tasks / weeks if weeks > 0 else 0
    else:
        velocity = None
    
    return {
        'summary': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'velocity': velocity
        },
        'status_breakdown': list(status_breakdown),
        'priority_breakdown': list(priority_breakdown),
        'time_tracking': {
            'total_estimated_hours': float(total_estimated),
            'total_actual_hours': float(total_actual),
            'variance': float(total_actual - total_estimated),
            'efficiency': (float(total_estimated) / float(total_actual) * 100) if total_actual > 0 else 0
        },
        'team_performance': list(team_stats),
        'bottlenecks': detect_task_bottlenecks(project)
    }