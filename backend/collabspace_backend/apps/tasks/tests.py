"""
CollabSpace AI - Tasks Module Tests
Comprehensive test suite for all task operations.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from decimal import Decimal

from apps.projects.models import Project
from .models import Task, TaskDependency, TaskComment, TaskAttachment, TimeEntry
from .views import TaskTemplate

User = get_user_model()


class TaskModelTestCase(TestCase):
    """Test Task model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            owner=self.user
        )
        
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            description='Test Description',
            status='todo',
            priority='medium',
            created_by=self.user,
            estimated_hours=Decimal('8.00')
        )
    
    def test_task_creation(self):
        """Test task is created correctly."""
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.status, 'todo')
        self.assertEqual(self.task.priority, 'medium')
        self.assertTrue(self.task.is_active)
    
    def test_actual_hours_calculation(self):
        """Test actual hours calculation from time entries."""
        # Create time entries
        TimeEntry.objects.create(
            task=self.task,
            user=self.user,
            hours=Decimal('2.5'),
            date=timezone.now().date()
        )
        TimeEntry.objects.create(
            task=self.task,
            user=self.user,
            hours=Decimal('3.5'),
            date=timezone.now().date()
        )
        
        self.assertEqual(self.task.actual_hours, Decimal('6.0'))
    
    def test_time_remaining_calculation(self):
        """Test time remaining calculation."""
        TimeEntry.objects.create(
            task=self.task,
            user=self.user,
            hours=Decimal('5.0'),
            date=timezone.now().date()
        )
        
        remaining = self.task.get_time_remaining()
        self.assertEqual(remaining, Decimal('3.0'))
    
    def test_subtask_creation(self):
        """Test subtask hierarchy."""
        subtask = Task.objects.create(
            project=self.project,
            title='Subtask 1',
            parent_task=self.task,
            created_by=self.user
        )
        
        self.assertEqual(subtask.parent_task, self.task)
        self.assertEqual(self.task.subtasks.count(), 1)
        self.assertFalse(subtask.is_root_task())
        self.assertTrue(self.task.is_root_task())
    
    def test_subtask_progress(self):
        """Test subtask progress calculation."""
        # Create subtasks
        Task.objects.create(
            project=self.project,
            title='Subtask 1',
            parent_task=self.task,
            status='done',
            created_by=self.user
        )
        Task.objects.create(
            project=self.project,
            title='Subtask 2',
            parent_task=self.task,
            status='todo',
            created_by=self.user
        )
        
        progress = self.task.get_subtask_progress_percentage()
        self.assertEqual(progress, 50.0)
    
    def test_is_overdue(self):
        """Test overdue detection."""
        # Set due date in the past
        self.task.due_date = timezone.now() - timedelta(days=1)
        self.task.save()
        
        self.assertTrue(self.task.is_overdue())
        
        # Mark as done
        self.task.status = 'done'
        self.task.save()
        
        self.assertFalse(self.task.is_overdue())


class TaskDependencyTestCase(TestCase):
    """Test task dependency functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        
        self.task1 = Task.objects.create(
            project=self.project,
            title='Task 1',
            created_by=self.user
        )
        
        self.task2 = Task.objects.create(
            project=self.project,
            title='Task 2',
            created_by=self.user
        )
    
    def test_dependency_creation(self):
        """Test creating task dependency."""
        dependency = TaskDependency.objects.create(
            task=self.task2,
            depends_on=self.task1,
            dependency_type='blocks'
        )
        
        self.assertEqual(dependency.task, self.task2)
        self.assertEqual(dependency.depends_on, self.task1)
    
    def test_is_blocked(self):
        """Test blocked task detection."""
        # Task2 depends on Task1
        TaskDependency.objects.create(
            task=self.task2,
            depends_on=self.task1,
            dependency_type='blocks'
        )
        
        # Task1 not done, so Task2 is blocked
        self.assertTrue(self.task2.is_blocked())
        
        # Complete Task1
        self.task1.status = 'done'
        self.task1.save()
        
        # Task2 should not be blocked anymore
        self.assertFalse(self.task2.is_blocked())
    
    def test_circular_dependency_prevention(self):
        """Test that circular dependencies are prevented."""
        # Create dependency: Task2 depends on Task1
        TaskDependency.objects.create(
            task=self.task2,
            depends_on=self.task1,
            dependency_type='blocks'
        )
        
        # Try to create circular dependency: Task1 depends on Task2
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            dependency = TaskDependency(
                task=self.task1,
                depends_on=self.task2,
                dependency_type='blocks'
            )
            dependency.full_clean()


class TaskAPITestCase(APITestCase):
    """Test Task API endpoints."""
    
    def setUp(self):
        """Set up test data and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            status='todo',
            priority='medium',
            created_by=self.user
        )
    
    def test_list_tasks(self):
        """Test listing tasks."""
        response = self.client.get('/api/tasks/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_create_task(self):
        """Test creating a task."""
        data = {
            'project': self.project.id,
            'title': 'New Task',
            'description': 'New Description',
            'status': 'todo',
            'priority': 'high'
        }
        
        response = self.client.post('/api/tasks/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Task')
    
    def test_update_task(self):
        """Test updating a task."""
        data = {
            'title': 'Updated Task',
            'priority': 'urgent'
        }
        
        response = self.client.patch(f'/api/tasks/{self.task.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Task')
        self.assertEqual(response.data['priority'], 'urgent')
    
    def test_assign_task(self):
        """Test assigning task to user."""
        response = self.client.post(
            f'/api/tasks/{self.task.id}/assign_task/',
            {'user_id': self.user.id}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.assigned_to, self.user)
    
    def test_update_status(self):
        """Test updating task status."""
        response = self.client.post(
            f'/api/tasks/{self.task.id}/update_status/',
            {'status': 'in_progress'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')
    
    def test_add_comment(self):
        """Test adding comment to task."""
        response = self.client.post(
            f'/api/tasks/{self.task.id}/add_comment/',
            {'content': 'Test comment'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.task.comments.count(), 1)
    
    def test_log_time(self):
        """Test logging time entry."""
        response = self.client.post(
            f'/api/tasks/{self.task.id}/log_time/',
            {
                'hours': 2.5,
                'description': 'Worked on implementation',
                'date': timezone.now().date().isoformat()
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.task.time_entries.count(), 1)
    
    def test_duplicate_task(self):
        """Test duplicating a task."""
        response = self.client.post(
            f'/api/tasks/{self.task.id}/duplicate/',
            {
                'include_subtasks': False,
                'new_title': 'Duplicated Task'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
    
    def test_bulk_update(self):
        """Test bulk updating tasks."""
        task2 = Task.objects.create(
            project=self.project,
            title='Task 2',
            created_by=self.user
        )
        
        response = self.client.post(
            '/api/tasks/bulk_operations/',
            {
                'task_ids': [self.task.id, task2.id],
                'operation': 'update_status',
                'status': 'in_progress'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['affected_count'], 2)
    
    def test_reorder_tasks(self):
        """Test reordering tasks (drag and drop)."""
        task2 = Task.objects.create(
            project=self.project,
            title='Task 2',
            position=1,
            created_by=self.user
        )
        
        response = self.client.post(
            '/api/tasks/reorder/',
            {
                'task_id': self.task.id,
                'new_position': 1
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.position, 1)
    
    def test_advanced_search(self):
        """Test advanced task search."""
        response = self.client.post(
            '/api/tasks/advanced_search/',
            {
                'query': 'Test',
                'search_fields': ['title', 'description'],
                'filters': {
                    'status': ['todo']
                },
                'limit': 10
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_task_analytics(self):
        """Test task analytics endpoint."""
        response = self.client.get(
            f'/api/tasks/analytics/?project={self.project.id}&group_by=status'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('grouped_data', response.data)
    
    def test_my_tasks(self):
        """Test getting current user's tasks."""
        self.task.assigned_to = self.user
        self.task.save()
        
        response = self.client.get('/api/tasks/my_tasks/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('assigned_to_me', response.data)


class TaskTemplateTestCase(APITestCase):
    """Test task template functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        
        self.template = TaskTemplate.objects.create(
            name='Bug Fix Template',
            title_template='Fix: {issue_description}',
            description_template='Bug in {project_name}',
            default_priority='high',
            category='Bug Fix',
            created_by=self.user
        )
    
    def test_list_templates(self):
        """Test listing templates."""
        response = self.client.get('/api/templates/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_create_template(self):
        """Test creating a template."""
        data = {
            'name': 'Feature Template',
            'title_template': 'Feature: {feature_name}',
            'description_template': 'Implement {feature_name}',
            'default_priority': 'medium',
            'category': 'Feature'
        }
        
        response = self.client.post('/api/templates/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Feature Template')
    
    def test_instantiate_template(self):
        """Test creating task from template."""
        response = self.client.post(
            f'/api/templates/{self.template.id}/instantiate/',
            {
                'project_id': self.project.id,
                'template_vars': {
                    'issue_description': 'Login not working',
                    'project_name': self.project.name
                }
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Fix: Login not working', response.data['title'])
        
        # Check usage count increased
        self.template.refresh_from_db()
        self.assertEqual(self.template.usage_count, 1)
    
    def test_popular_templates(self):
        """Test getting popular templates."""
        response = self.client.get('/api/templates/popular/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_templates_by_category(self):
        """Test getting templates grouped by category."""
        response = self.client.get('/api/templates/by_category/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Bug Fix', response.data)


class TaskFilterTestCase(APITestCase):
    """Test task filtering."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        
        # Create tasks with different attributes
        Task.objects.create(
            project=self.project,
            title='High Priority Task',
            status='todo',
            priority='high',
            tags=['urgent', 'bug'],
            created_by=self.user
        )
        
        Task.objects.create(
            project=self.project,
            title='Medium Priority Task',
            status='in_progress',
            priority='medium',
            tags=['feature'],
            created_by=self.user,
            assigned_to=self.user
        )
    
    def test_filter_by_status(self):
        """Test filtering by status."""
        response = self.client.get('/api/tasks/?status=todo')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertEqual(task['status'], 'todo')
    
    def test_filter_by_priority(self):
        """Test filtering by priority."""
        response = self.client.get('/api/tasks/?priority=high')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertEqual(task['priority'], 'high')
    
    def test_filter_by_tags(self):
        """Test filtering by tags."""
        response = self.client.get('/api/tasks/?tags=urgent,bug')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_filter_assigned_to_me(self):
        """Test filtering tasks assigned to current user."""
        response = self.client.get('/api/tasks/?assigned_to_me=true')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for task in response.data['results']:
            self.assertIsNotNone(task['assigned_to'])
    
    def test_search(self):
        """Test search functionality."""
        response = self.client.get('/api/tasks/?search=High')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_ordering(self):
        """Test result ordering."""
        response = self.client.get('/api/tasks/?ordering=-priority')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # High priority should come first
        if len(response.data['results']) >= 2:
            self.assertEqual(response.data['results'][0]['priority'], 'high')