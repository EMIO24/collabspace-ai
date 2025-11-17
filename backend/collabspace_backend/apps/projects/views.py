"""
Project views for CollabSpace AI.
"""

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
import csv
import json
from io import StringIO

from .models import Project, ProjectMember, ProjectLabel, ProjectTemplate, ProjectActivity
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer, ProjectCreateSerializer,
    ProjectUpdateSerializer, ProjectMemberSerializer, ProjectLabelSerializer,
    AddProjectMemberSerializer, ProjectStatsSerializer, ProjectActivitySerializer,
    ProjectTemplateSerializer
)
from apps.core.permissions import IsWorkspaceMember


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for project CRUD operations.
    
    Endpoints:
    - GET /api/projects/ - List projects
    - POST /api/projects/ - Create project
    - GET /api/projects/{id}/ - Retrieve project
    - PUT /api/projects/{id}/ - Update project
    - PATCH /api/projects/{id}/ - Partial update
    - DELETE /api/projects/{id}/ - Delete project
    """
    
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Get projects user has access to."""
        user = self.request.user
        
        # Get projects from workspaces user is a member of
        queryset = Project.objects.filter(
            Q(workspace__members__user=user) | Q(owner=user),
            is_deleted=False
        ).select_related(
            'workspace', 'owner'
        ).prefetch_related(
            'members', 'labels'
        ).distinct()
        
        # Filter by workspace
        workspace_id = self.request.query_params.get('workspace')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        return ProjectDetailSerializer
    
    def perform_destroy(self, instance):
        """Soft delete project."""
        instance.soft_delete(user=self.request.user)
        
        # Log activity
        ProjectActivity.objects.create(
            project=instance,
            user=self.request.user,
            action='deleted',
            description=f'{self.request.user.get_full_name()} deleted project {instance.name}'
        )
    
    @action(detail=True, methods=['get'])
    def board(self, request, id=None):
        """
        Get Kanban board view of project.
        
        GET /api/projects/{id}/board/
        """
        project = self.get_object()
        
        # This will be implemented when tasks module is added
        # from apps.tasks.models import Task
        # tasks_by_status = {}
        # for status_choice in ['todo', 'in_progress', 'review', 'done']:
        #     tasks = Task.objects.filter(
        #         project=project,
        #         status=status_choice,
        #         is_deleted=False
        #     ).select_related('assigned_to', 'created_by')
        #     tasks_by_status[status_choice] = TaskSerializer(tasks, many=True).data
        
        return Response({
            'project': ProjectDetailSerializer(project).data,
            'board': {
                'todo': [],
                'in_progress': [],
                'review': [],
                'done': [],
            }
        })
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, id=None):
        """
        Get Gantt/timeline view of project.
        
        GET /api/projects/{id}/timeline/
        """
        project = self.get_object()
        
        # This will be implemented when tasks module is added
        # tasks = Task.objects.filter(
        #     project=project,
        #     is_deleted=False
        # ).order_by('start_date')
        
        timeline_data = {
            'project': {
                'name': project.name,
                'start_date': project.start_date,
                'end_date': project.end_date,
                'progress': float(project.progress),
            },
            'tasks': []  # Will be populated with task timeline data
        }
        
        return Response(timeline_data)
    
    @action(detail=True, methods=['get'])
    def calendar(self, request, id=None):
        """
        Get calendar view of project tasks.
        
        GET /api/projects/{id}/calendar/
        """
        project = self.get_object()
        
        # Get month from query params
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        # This will be implemented when tasks module is added
        calendar_data = {
            'project_id': str(project.id),
            'project_name': project.name,
            'events': []  # Will contain tasks with due dates
        }
        
        return Response(calendar_data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, id=None):
        """
        Duplicate project with optional settings.
        
        POST /api/projects/{id}/duplicate/
        Body: {
            "name": "New Project Name",
            "include_tasks": true,
            "include_members": true,
            "include_labels": true
        }
        """
        original_project = self.get_object()
        
        # Get options
        new_name = request.data.get('name', f'{original_project.name} (Copy)')
        include_tasks = request.data.get('include_tasks', False)
        include_members = request.data.get('include_members', True)
        include_labels = request.data.get('include_labels', True)
        
        # Create duplicate project
        new_project = Project.objects.create(
            workspace=original_project.workspace,
            name=new_name,
            description=original_project.description,
            owner=request.user,
            status='active',
            priority=original_project.priority,
            color=original_project.color,
            icon=original_project.icon,
            is_public=original_project.is_public,
            settings=original_project.settings.copy()
        )
        
        # Add owner as member
        new_project.add_member(request.user, role='owner')
        
        # Duplicate members
        if include_members:
            for member in original_project.members.all():
                if member.user != request.user:  # Owner already added
                    new_project.add_member(member.user, role=member.role, added_by=request.user)
        
        # Duplicate labels
        if include_labels:
            for label in original_project.labels.all():
                ProjectLabel.objects.create(
                    project=new_project,
                    name=label.name,
                    color=label.color,
                    description=label.description,
                    created_by=request.user
                )
        
        # Duplicate tasks (when tasks module is added)
        # if include_tasks:
        #     for task in original_project.tasks.filter(is_deleted=False):
        #         # Create duplicate task
        
        # Log activity
        ProjectActivity.objects.create(
            project=new_project,
            user=request.user,
            action='created',
            description=f'{request.user.get_full_name()} duplicated project from {original_project.name}'
        )
        
        return Response(
            ProjectDetailSerializer(new_project, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def archive(self, request, id=None):
        """
        Archive project.
        
        POST /api/projects/{id}/archive/
        """
        project = self.get_object()
        project.archive()
        
        # Log activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            action='archived',
            description=f'{request.user.get_full_name()} archived project'
        )
        
        return Response({'message': 'Project archived successfully'})
    
    @action(detail=True, methods=['post'])
    def restore(self, request, id=None):
        """
        Restore archived project.
        
        POST /api/projects/{id}/restore/
        """
        project = self.get_object()
        project.restore()
        
        # Log activity
        ProjectActivity.objects.create(
            project=project,
            user=request.user,
            action='restored',
            description=f'{request.user.get_full_name()} restored project'
        )
        
        return Response({'message': 'Project restored successfully'})
    
    @action(detail=True, methods=['get'])
    def export(self, request, id=None):
        """
        Export project data.
        
        GET /api/projects/{id}/export/?format=json|csv
        """
        project = self.get_object()
        export_format = request.query_params.get('format', 'json')
        
        if export_format == 'csv':
            # Export as CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Project Name', 'Description', 'Status', 'Priority', 'Progress', 'Members', 'Tasks'])
            
            # Write project data
            writer.writerow([
                project.name,
                project.description,
                project.status,
                project.priority,
                f'{project.progress}%',
                project.member_count,
                project.task_count
            ])
            
            response = Response(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{project.slug}.csv"'
            return response
        
        else:
            # Export as JSON
            data = {
                'project': ProjectDetailSerializer(project, context={'request': request}).data,
                'members': ProjectMemberSerializer(project.members.all(), many=True).data,
                'labels': ProjectLabelSerializer(project.labels.all(), many=True).data,
                'tasks': [],  # Will be added when tasks module exists
                'exported_at': timezone.now().isoformat()
            }
            
            response = Response(data)
            response['Content-Disposition'] = f'attachment; filename="{project.slug}.json"'
            return response


class ProjectMemberViewSet(viewsets.ViewSet):
    """
    ViewSet for project member management.
    
    Endpoints:
    - GET /api/projects/{project_id}/members/ - List members
    - POST /api/projects/{project_id}/members/ - Add member
    - DELETE /api/projects/{project_id}/members/{user_id}/ - Remove member
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request, project_id=None):
        """List project members."""
        project = get_object_or_404(Project, id=project_id, is_deleted=False)
        
        # Check permission
        if not project.is_member(request.user):
            return Response(
                {'error': 'You do not have access to this project'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        members = project.members.all()
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    def create(self, request, project_id=None):
        """Add member to project."""
        project = get_object_or_404(Project, id=project_id, is_deleted=False)
        
        # Check permission
        if not project.is_admin(request.user):
            return Response(
                {'error': 'Only project admins can add members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AddProjectMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user_id']
        role = serializer.validated_data['role']
        
        try:
            member = project.add_member(user, role=role, added_by=request.user)
            
            # Log activity
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                action='member_added',
                description=f'{request.user.get_full_name()} added {user.get_full_name()} as {role}'
            )
            
            return Response(
                ProjectMemberSerializer(member).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, project_id=None, user_id=None):
        """Remove member from project."""
        project = get_object_or_404(Project, id=project_id, is_deleted=False)
        
        # Check permission
        if not project.is_admin(request.user):
            return Response(
                {'error': 'Only project admins can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = get_object_or_404(User, id=user_id)
            
            project.remove_member(user)
            
            # Log activity
            ProjectActivity.objects.create(
                project=project,
                user=request.user,
                action='member_removed',
                description=f'{request.user.get_full_name()} removed {user.get_full_name()}'
            )
            
            return Response({'message': 'Member removed successfully'})
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProjectLabelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for project labels.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectLabelSerializer
    
    def get_queryset(self):
        """Get labels for project."""
        project_id = self.kwargs.get('project_id')
        return ProjectLabel.objects.filter(project_id=project_id)
    
    def perform_create(self, serializer):
        """Create label with project and creator."""
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        serializer.save(project=project, created_by=self.request.user)


class ProjectStatsView(views.APIView):
    """
    Get project statistics.
    
    GET /api/projects/{id}/stats/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get project stats."""
        project = get_object_or_404(Project, id=id, is_deleted=False)
        
        # Check permission
        if not project.is_member(request.user):
            return Response(
                {'error': 'You do not have access to this project'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = project.get_statistics()
        serializer = ProjectStatsSerializer(stats)
        return Response(serializer.data)


class ProjectActivityView(views.APIView):
    """
    Get project activity feed.
    
    GET /api/projects/{id}/activity/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get project activity."""
        project = get_object_or_404(Project, id=id, is_deleted=False)
        
        # Check permission
        if not project.is_member(request.user):
            return Response(
                {'error': 'You do not have access to this project'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        activities = project.activities.all()[:50]  # Last 50 activities
        serializer = ProjectActivitySerializer(activities, many=True)
        return Response(serializer.data)