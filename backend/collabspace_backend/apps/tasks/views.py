"""
CollabSpace AI - Tasks Module Views
Comprehensive ViewSets with all task management functionality merged.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Count, Sum, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
import csv
from io import StringIO

# Assuming these imports are correct relative to the file's location
from .models import Task, TaskComment, TaskAttachment, TimeEntry, TaskDependency, TaskTemplate
from .serializers import (
    TaskListSerializer, TaskDetailSerializer, TaskCreateSerializer,
    TaskUpdateSerializer, TaskStatusUpdateSerializer, TaskCommentSerializer,
    TaskAttachmentSerializer, TimeEntrySerializer, TaskDependencySerializer,
    BulkTaskSerializer, TaskDuplicateSerializer,
    TaskReorderSerializer, BulkTaskOperationSerializer, TaskSearchSerializer,
    TaskAnalyticsSerializer, TaskTemplateSerializer, TaskTemplateInstantiateSerializer
)
from .filters import TaskFilter
from .utils import auto_assign_task, generate_task_report
from apps.core.permissions import IsProjectMember


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task management with comprehensive CRUD and custom actions.
    This class combines all functionality from the original TaskViewSet
    and the extended TaskViewSetExtended.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'position']
    ordering = ['position', '-created_at']

    def get_queryset(self):
        """
        Get tasks with optimized queries.
        Filter by project, assignment, creation, or root tasks based on query params.
        """
        queryset = Task.objects.filter(is_active=True).select_related(
            'project', 'assigned_to', 'created_by', 'parent_task'
        ).prefetch_related(
            'subtasks', 'comments', 'attachments', 'time_entries',
            'dependencies', 'dependents'
        )

        request = self.request

        # Filter by project if specified
        project_id = request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Filter by assigned user
        assigned_to_me = request.query_params.get('assigned_to_me')
        if assigned_to_me and assigned_to_me.lower() == 'true':
            queryset = queryset.filter(assigned_to=request.user)

        # Filter by created by user
        created_by_me = request.query_params.get('created_by_me')
        if created_by_me and created_by_me.lower() == 'true':
            queryset = queryset.filter(created_by=request.user)

        # Filter root tasks only
        root_only = request.query_params.get('root_only')
        if root_only and root_only.lower() == 'true':
            queryset = queryset.filter(parent_task__isnull=True)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        elif self.action == 'update_status':
            return TaskStatusUpdateSerializer
        elif self.action in ['bulk_update', 'bulk_delete']:
            return BulkTaskSerializer
        elif self.action == 'duplicate':
            return TaskDuplicateSerializer
        # Note: 'reorder', 'bulk_operations', 'advanced_search', 'analytics', 'my_tasks'
        # use dedicated or internal serializers, so TaskDetailSerializer is the fallback.
        return TaskDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()  # perform_create() is called automatically

        # Return full detail response
        output = TaskDetailSerializer(task, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)


    # ============================================================================
    # 1. Standard Custom Actions (from original TaskViewSet)
    # ============================================================================

    @action(detail=True, methods=['post'])
    def assign_task(self, request, pk=None):
        """
        Assign task to a user.
        POST /api/tasks/{id}/assign_task/
        Body: {"user_id": 123}
        """
        task = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            task.assigned_to = user
            task.save()

            serializer = TaskDetailSerializer(task, context={'request': request})
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    # Auto-assign if not specified
        if not task.assigned_to:
            assigned_user = auto_assign_task(task, task.project)
            if assigned_user:
                task.assigned_to = assigned_user
                task.save()

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update task status.
        POST /api/tasks/{id}/update_status/
        Body: {"status": "in_progress"}
        """
        task = self.get_object()
        serializer = TaskStatusUpdateSerializer(
            task, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return updated task
        task.refresh_from_db()
        response_serializer = TaskDetailSerializer(task, context={'request': request})
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """
        Add a comment to a task.
        POST /api/tasks/{id}/add_comment/
        Body: {"content": "Comment text"}
        """
        task = self.get_object()
        data = request.data.copy()
        data['task'] = task.id
        data['user'] = request.user.id # Ensure user is set via data for the serializer

        serializer = TaskCommentSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # Note: perform_create in TaskCommentViewSet handles setting user.
        # Since we are using the serializer here, we need to ensure the user is linked
        # The serializer should handle setting the user, but we ensure it's available.
        comment = serializer.save(user=request.user)

        return Response(
            TaskCommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def upload_attachment(self, request, pk=None):
        """
        Upload an attachment to a task.
        POST /api/tasks/{id}/upload_attachment/
        Body: {"file_name": "doc.pdf", "file_url": "https://...", "file_size": 1024, "file_type": "application/pdf"}
        """
        task = self.get_object()
        data = request.data.copy()
        data['task'] = task.id

        serializer = TaskAttachmentSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(uploaded_by=request.user)

        return Response(
            TaskAttachmentSerializer(attachment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def log_time(self, request, pk=None):
        """
        Log time entry for a task.
        POST /api/tasks/{id}/log_time/
        Body: {"hours": 2.5, "description": "Work description", "date": "2024-01-15"}
        """
        task = self.get_object()
        data = request.data.copy()
        data['task'] = task.id

        serializer = TimeEntrySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        time_entry = serializer.save(user=request.user)

        return Response(
            TimeEntrySerializer(time_entry, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        """
        Add a dependency to a task.
        POST /api/tasks/{id}/add_dependency/
        Body: {"depends_on": 456, "dependency_type": "blocks"}
        """
        task = self.get_object()
        data = request.data.copy()
        data['task'] = task.id

        serializer = TaskDependencySerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        dependency = serializer.save()

        return Response(
            TaskDependencySerializer(dependency, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a task with optional related data.
        POST /api/tasks/{id}/duplicate/
        Body: {
            "include_subtasks": true,
            "include_attachments": true,
            "include_comments": false,
            "new_title": "Copy of Task"
        }
        """
        task = self.get_object()
        serializer = TaskDuplicateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        duplicate_task = serializer.duplicate_task(task)

        return Response(
            TaskDetailSerializer(duplicate_task, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        Bulk update multiple tasks.
        POST /api/tasks/bulk_update/
        Body: {
            "task_ids": [1, 2, 3],
            "status": "in_progress",
            "priority": "high",
            "assigned_to_id": 5
        }
        """
        serializer = BulkTaskSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        updated_tasks = serializer.update_tasks(serializer.validated_data)

        return Response({
            'message': f'Successfully updated {updated_tasks.count()} tasks',
            'updated_task_ids': list(updated_tasks.values_list('id', flat=True))
        })

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """
        Bulk delete (soft delete) multiple tasks.
        POST /api/tasks/bulk_delete/
        Body: {"task_ids": [1, 2, 3]}
        """
        task_ids = request.data.get('task_ids', [])

        if not task_ids:
            return Response(
                {'error': 'task_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BulkTaskSerializer(data={'task_ids': task_ids})
        serializer.is_valid(raise_exception=True)

        deleted_ids = serializer.delete_tasks(task_ids)

        return Response({
            'message': f'Successfully deleted {len(deleted_ids)} tasks',
            'deleted_task_ids': deleted_ids
        })

    @action(detail=True, methods=['get'])
    def subtasks(self, request, pk=None):
        """
        Get all subtasks for a task (recursive).
        GET /api/tasks/{id}/subtasks/
        """
        task = self.get_object()
        # Assumes task.get_all_subtasks() method exists on the Task model
        subtasks = task.get_all_subtasks()
        serializer = TaskListSerializer(subtasks, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        Get task timeline (comments, status changes, time entries).
        GET /api/tasks/{id}/timeline/
        """
        task = self.get_object()

        # Combine different activities into timeline
        timeline = []

        # Add comments
        for comment in task.comments.filter(is_active=True).select_related('user'):
            timeline.append({
                'type': 'comment',
                'timestamp': comment.created_at,
                'user': comment.user.username,
                'data': TaskCommentSerializer(comment).data
            })

        # Add time entries
        for entry in task.time_entries.all().select_related('user'):
            timeline.append({
                'type': 'time_entry',
                'timestamp': entry.created_at,
                'user': entry.user.username,
                'data': TimeEntrySerializer(entry).data
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)

        return Response(timeline)

    # ============================================================================
    # 2. Advanced Custom Actions (from TaskViewSetExtended)
    # ============================================================================

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder tasks (drag and drop support).
        POST /api/tasks/reorder/
        Body: {
            "task_id": 123,
            "new_position": 5,
            "parent_task_id": 456  // optional
        }
        """
        serializer = TaskReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task_id = serializer.validated_data['task_id']
        new_position = serializer.validated_data['new_position']
        parent_task_id = serializer.validated_data.get('parent_task_id')

        with transaction.atomic():
            # Use select_for_update to lock rows during reorder operation
            task = Task.objects.select_for_update().get(id=task_id)
            old_position = task.position
            old_parent = task.parent_task_id

            # Get sibling tasks (same project, same new parent)
            siblings = Task.objects.filter(
                project=task.project,
                parent_task_id=parent_task_id,
                is_active=True
            ).exclude(id=task_id).order_by('position').select_for_update()

            # Update parent if changed
            if parent_task_id != old_parent:
                task.parent_task_id = parent_task_id

            # Reorder siblings only if position or parent changed
            if new_position != old_position or parent_task_id != old_parent:
                # Re-sequence positions
                position = 0
                updated_siblings = []
                for sibling in siblings:
                    # Skip the new position for the moved task
                    if position == new_position:
                        position += 1
                    
                    if sibling.position != position:
                        sibling.position = position
                        updated_siblings.append(sibling)
                    position += 1
                
                # Bulk update siblings
                if updated_siblings:
                    Task.objects.bulk_update(updated_siblings, ['position'])

                # Set new position for moved task
                task.position = new_position
                task.save(update_fields=['position', 'parent_task'])

        return Response({
            'message': 'Task reordered successfully',
            'task_id': task_id,
            'new_position': new_position,
            'parent_task_id': parent_task_id
        })

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """
        Perform complex bulk operations on multiple tasks (e.g., add tags, move project).
        POST /api/tasks/bulk_operations/
        Body: {
            "task_ids": [1, 2, 3],
            "operation": "update_status",
            "status": "in_progress"
        }
        """
        serializer = BulkTaskOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task_ids = serializer.validated_data['task_ids']
        operation = serializer.validated_data['operation']

        with transaction.atomic():
            tasks = Task.objects.select_for_update().filter(
                id__in=task_ids, is_active=True
            )

            result = {'success': True, 'affected_count': 0, 'message': ''}

            if operation == 'update_status':
                status_value = serializer.validated_data.get('status')
                tasks.update(status=status_value)
                result['affected_count'] = tasks.count()
                result['message'] = f'Updated status to {status_value}'

            elif operation == 'update_priority':
                priority = serializer.validated_data.get('priority')
                tasks.update(priority=priority)
                result['affected_count'] = tasks.count()
                result['message'] = f'Updated priority to {priority}'

            elif operation == 'assign':
                assigned_to_id = serializer.validated_data.get('assigned_to_id')
                tasks.update(assigned_to_id=assigned_to_id)
                result['affected_count'] = tasks.count()
                result['message'] = 'Tasks assigned'

            elif operation == 'add_tags':
                tags = serializer.validated_data.get('tags', [])
                for task in tasks:
                    existing_tags = set(task.tags)
                    existing_tags.update(tags)
                    task.tags = list(existing_tags)
                    task.save(update_fields=['tags'])
                result['affected_count'] = tasks.count()
                result['message'] = f'Added tags: {", ".join(tags)}'

            elif operation == 'remove_tags':
                tags = serializer.validated_data.get('tags', [])
                for task in tasks:
                    existing_tags = set(task.tags)
                    existing_tags.difference_update(tags)
                    task.tags = list(existing_tags)
                    task.save(update_fields=['tags'])
                result['affected_count'] = tasks.count()
                result['message'] = f'Removed tags: {", ".join(tags)}'

            elif operation == 'set_due_date':
                due_date = serializer.validated_data.get('due_date')
                tasks.update(due_date=due_date)
                result['affected_count'] = tasks.count()
                result['message'] = 'Updated due dates'

            elif operation == 'move_to_project':
                project_id = serializer.validated_data.get('project_id')
                tasks.update(project_id=project_id, parent_task=None) # Set parent_task to None when moving to another project
                result['affected_count'] = tasks.count()
                result['message'] = f'Moved to project {project_id}'

            elif operation == 'archive':
                tasks.update(is_active=False)
                result['affected_count'] = tasks.count()
                result['message'] = 'Tasks archived'

            elif operation == 'delete':
                count = tasks.count()
                # tasks.delete() performs a hard delete, adjust if you use soft delete manager
                tasks.delete()
                result['affected_count'] = count
                result['message'] = 'Tasks deleted'

            elif operation == 'duplicate':
                duplicated_tasks = []
                for task in tasks:
                    duplicate = Task.objects.create(
                        project=task.project,
                        title=f"{task.title} (Copy)",
                        description=task.description,
                        status=Task.STATUS_TODO,
                        priority=task.priority,
                        assigned_to=task.assigned_to,
                        created_by=request.user,
                        estimated_hours=task.estimated_hours,
                        # Assuming tags and metadata are JSONField/ArrayField and can be copied
                        tags=task.tags.copy() if task.tags else [],
                        metadata=task.metadata.copy() if task.metadata else {}
                    )
                    duplicated_tasks.append(duplicate.id)
                result['affected_count'] = len(duplicated_tasks)
                result['duplicated_ids'] = duplicated_tasks
                result['message'] = f'Duplicated {len(duplicated_tasks)} tasks'

            elif operation == 'export':
                # Export to CSV
                output = StringIO()
                writer = csv.writer(output)
                writer.writerow([
                    'ID', 'Title', 'Status', 'Priority', 'Assigned To',
                    'Due Date', 'Estimated Hours', 'Tags'
                ])

                for task in tasks.select_related('assigned_to'):
                    writer.writerow([
                        task.id,
                        task.title,
                        task.status,
                        task.priority,
                        task.assigned_to.username if task.assigned_to else '',
                        task.due_date.isoformat() if task.due_date else '',
                        task.estimated_hours or '',
                        ', '.join(task.tags)
                    ])

                result['affected_count'] = tasks.count()
                result['csv_data'] = output.getvalue()
                result['message'] = 'Tasks exported'
                # Must return here to pass the CSV data instead of default JSON response
                return Response(result)
            
            # Default response for all operations except 'export'
            return Response(result)
            
        # Re-raise exceptions if transaction fails

    @action(detail=False, methods=['post'])
    def advanced_search(self, request):
        """
        Advanced task search with multiple criteria.
        POST /api/tasks/advanced_search/
        Body: {
            "query": "bug fix",
            "search_fields": ["title", "description", "tags"],
            "filters": {
                "status": ["todo", "in_progress"],
                "priority": ["high", "urgent"]
            },
            "limit": 50
        }
        """
        serializer = TaskSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        search_fields = serializer.validated_data['search_fields']
        filters = serializer.validated_data.get('filters', {})
        limit = serializer.validated_data['limit']

        # Build search query
        q_objects = Q()
        if 'title' in search_fields:
            q_objects |= Q(title__icontains=query)
        if 'description' in search_fields:
            q_objects |= Q(description__icontains=query)
        # Note: tags__contains requires PostgreSQL's ArrayField/JSONField or a custom solution
        if 'tags' in search_fields:
            q_objects |= Q(tags__contains=[query])
        # Note: comments search requires a join to TaskComment and distinct()
        if 'comments' in search_fields:
            q_objects |= Q(comments__content__icontains=query)

        queryset = Task.objects.filter(q_objects, is_active=True).distinct().select_related(
             'project', 'assigned_to', 'created_by', 'parent_task'
        )

        # Apply additional filters
        if 'status' in filters:
            queryset = queryset.filter(status__in=filters['status'])
        if 'priority' in filters:
            queryset = queryset.filter(priority__in=filters['priority'])
        if 'assigned_to' in filters:
            queryset = queryset.filter(assigned_to_id__in=filters['assigned_to'])
        if 'project' in filters:
            queryset = queryset.filter(project_id__in=filters['project'])
        
        # Apply permission filtering (optional, based on IsProjectMember logic)
        queryset = self.filter_queryset(queryset)

        # Limit results
        if limit:
            queryset = queryset[:limit]

        # Serialize and return
        serializer = TaskListSerializer(
            queryset, many=True, context={'request': request}
        )

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get task analytics and insights.
        GET /api/tasks/analytics/?project=123&group_by=status
        """
        serializer = TaskAnalyticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        queryset = Task.objects.filter(is_active=True)

        # Apply filters
        validated_data = serializer.validated_data
        if validated_data.get('project_id'):
            queryset = queryset.filter(
                project_id=validated_data['project_id']
            )

        if validated_data.get('user_id'):
            user_id = validated_data['user_id']
            queryset = queryset.filter(
                Q(assigned_to_id=user_id) | Q(created_by_id=user_id)
            )

        if validated_data.get('start_date'):
            queryset = queryset.filter(
                created_at__gte=validated_data['start_date']
            )

        if validated_data.get('end_date'):
            # Filter up to the end of the specified end date
            end_date_inclusive = validated_data['end_date'] + timedelta(days=1)
            queryset = queryset.filter(
                created_at__lt=end_date_inclusive
            )

        group_by = validated_data['group_by']
        data = []

        # Generate analytics based on grouping
        if group_by == 'status':
            data = queryset.values('status').annotate(
                count=Count('id'),
                avg_hours=Avg('estimated_hours')
            ).order_by('status')

        elif group_by == 'priority':
            data = queryset.values('priority').annotate(
                count=Count('id'),
                avg_hours=Avg('estimated_hours')
            ).order_by('priority')

        elif group_by == 'assignee':
            # Use assigned_to_id for grouping, then fetch username separately if needed
            data = queryset.values(
                'assigned_to_id', 'assigned_to__username'
            ).annotate(
                count=Count('id'),
                completed=Count('id', filter=Q(status='done')),
                total_hours=Sum('estimated_hours')
            ).order_by('-count')

        elif group_by == 'date':
            # Note: For SQLite, DATE(created_at) won't work. For PostgreSQL, use TruncDate
            # Using extra for demonstration, assumes a database that supports DATE()
            data = queryset.extra(
                select={'date': 'DATE(created_at)'}
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

        elif group_by == 'tag':
            # Generic aggregation by tags (manual iteration, as ArrayAgg is Postgres-specific)
            tags_data = {}
            for task in queryset:
                for tag in task.tags:
                    if tag not in tags_data:
                        tags_data[tag] = {'tag': tag, 'count': 0}
                    tags_data[tag]['count'] += 1
            # Convert dictionary items to a list of dicts for the final response
            data = list(tags_data.values())

        # Calculate summary statistics (independent of grouping)
        summary = {
            'total_tasks': queryset.count(),
            'completed': queryset.filter(status='done').count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'overdue': queryset.filter(
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress', 'review']
            ).count(),
            'avg_estimated_hours': queryset.aggregate(
                avg=Avg('estimated_hours')
            )['avg'] or 0.0,
            'total_estimated_hours': queryset.aggregate(
                total=Sum('estimated_hours')
            )['total'] or 0.0
        }

        return Response({
            'summary': summary,
            'grouped_data': list(data)
        })

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """
        Get current user's tasks with smart grouping.
        GET /api/tasks/my_tasks/
        """
        user = request.user
        
        # Base queryset optimized for list view and filtering
        base_queryset = Task.objects.filter(is_active=True).select_related(
            'project', 'assigned_to', 'created_by'
        )

        result = {
            'assigned_to_me': [],
            'created_by_me': [],
            'due_today': [],
            'overdue': [],
            'in_progress': [],
            # 'watching' requires a separate TaskWatch model or similar. Left out for now.
        }

        # Assigned to me (Top 20)
        assigned = base_queryset.filter(assigned_to=user)[:20]
        result['assigned_to_me'] = TaskListSerializer(
            assigned, many=True, context={'request': request}
        ).data

        # Created by me (Top 20, excluding those assigned to me to avoid overlap)
        created = base_queryset.filter(created_by=user).exclude(assigned_to=user)[:20]
        result['created_by_me'] = TaskListSerializer(
            created, many=True, context={'request': request}
        ).data

        # Due today (Assigned or Created)
        today = timezone.localdate(timezone.now())
        due_today = base_queryset.filter(
            Q(assigned_to=user) | Q(created_by=user),
            due_date__date=today, # Filter by date part
            status__in=['todo', 'in_progress', 'review'],
        )
        result['due_today'] = TaskListSerializer(
            due_today, many=True, context={'request': request}
        ).data

        # Overdue (Assigned or Created)
        overdue = base_queryset.filter(
            Q(assigned_to=user) | Q(created_by=user),
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress', 'review'],
        )
        result['overdue'] = TaskListSerializer(
            overdue, many=True, context={'request': request}
        ).data

        # In progress (Assigned to me)
        in_progress = base_queryset.filter(
            assigned_to=user,
            status='in_progress',
        )
        result['in_progress'] = TaskListSerializer(
            in_progress, many=True, context={'request': request}
        ).data

        return Response(result)


# --- Independent ViewSets ---

class TaskCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing task comments."""

    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['created_at']

    def get_queryset(self):
        """Get comments with optimized queries. Filters by task_id if provided."""
        queryset = TaskComment.objects.filter(is_active=True).select_related(
            'task', 'user', 'parent_comment'
        ).prefetch_related('mentions', 'replies')
        
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
            
        return queryset

    def perform_create(self, serializer):
        """Set user on comment creation."""
        # Note: This is crucial for security and data integrity.
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies to a comment (Assumes get_all_replies() method exists on TaskComment model)."""
        comment = self.get_object()
        replies = comment.get_all_replies()
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing task attachments."""

    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        """Get attachments with optimized queries. Filters by task_id if provided."""
        queryset = TaskAttachment.objects.all().select_related(
            'task', 'uploaded_by'
        )

        # Filter by task if specified
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset

    def perform_create(self, serializer):
        """Set uploaded_by on attachment creation."""
        serializer.save(uploaded_by=self.request.user)


class TimeEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing time entries."""

    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering = ['-date', '-created_at']
    filterset_fields = ['task', 'user', 'date']

    def get_queryset(self):
        """Get time entries with optimized queries."""
        queryset = TimeEntry.objects.all().select_related('task', 'user')
        request = self.request

        # Filter by date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Filter by current user's entries
        my_entries = request.query_params.get('my_entries')
        if my_entries and my_entries.lower() == 'true':
            queryset = queryset.filter(user=request.user)

        return queryset

    def perform_create(self, serializer):
        """Set user on time entry creation."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get time entry summary for current user.
        GET /api/time-entries/summary/?start_date=2024-01-01&end_date=2024-01-31
        """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(user=request.user)

        total_hours = queryset.aggregate(total=Sum('hours'))['total'] or 0
        entries_count = queryset.count()

        # Group by task
        by_task = queryset.values(
            'task__id', 'task__title'
        ).annotate(
            total_hours=Sum('hours'),
            entries=Count('id')
        ).order_by('-total_hours')

        # Group by date
        by_date = queryset.values('date').annotate(
            total_hours=Sum('hours'),
            entries=Count('id')
        ).order_by('date')

        return Response({
            'total_hours': float(total_hours),
            'entries_count': entries_count,
            'by_task': list(by_task),
            'by_date': list(by_date)
        })


class TaskStatsView(APIView):
    """
    View for task statistics and analytics (Simpler version of TaskViewSet.analytics).
    GET /api/tasks/stats/?project=123
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get comprehensive task statistics."""
        project_id = request.query_params.get('project')

        # Base queryset
        queryset = Task.objects.filter(is_active=True)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Status distribution
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')

        # Priority distribution
        priority_counts = queryset.values('priority').annotate(
            count=Count('id')
        ).order_by('priority')

        # Assignment distribution
        assigned_counts = queryset.values(
            'assigned_to__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Overdue tasks
        overdue_count = queryset.filter(
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress', 'review']
        ).count()

        # Due soon (next 7 days)
        due_soon_count = queryset.filter(
            due_date__gte=timezone.now(),
            due_date__lt=timezone.now() + timedelta(days=7),
            status__in=['todo', 'in_progress', 'review']
        ).count()

        # Completion rate
        total_tasks = queryset.count()
        completed_tasks = queryset.filter(status='done').count()
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Time tracking stats
        time_stats = queryset.aggregate(
            total_estimated=Sum('estimated_hours'),
            avg_estimated=Avg('estimated_hours')
        )

        # Get actual hours through time entries
        total_actual_hours = TimeEntry.objects.filter(
            task__in=queryset
        ).aggregate(total=Sum('hours'))['total'] or 0

        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completion_rate, 2),
            'overdue_count': overdue_count,
            'due_soon_count': due_soon_count,
            'status_distribution': list(status_counts),
            'priority_distribution': list(priority_counts),
            'assignment_distribution': list(assigned_counts),
            'time_stats': {
                'total_estimated_hours': float(time_stats['total_estimated'] or 0),
                'avg_estimated_hours': float(time_stats['avg_estimated'] or 0),
                'total_actual_hours': float(total_actual_hours),
            }
        })


class TaskTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for task templates."""

    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_public']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'usage_count', 'created_at']
    ordering = ['-usage_count', 'name']

    def get_queryset(self):
        """Get templates available to user (created by user or public)."""
        user = self.request.user
        return TaskTemplate.objects.filter(
            Q(created_by=user) | Q(is_public=True),
            is_active=True # Assuming TaskTemplate has an is_active field
        ).select_related('created_by')

    def perform_create(self, serializer):
        """Set created_by on template creation."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def instantiate(self, request, pk=None):
        """
        Create a task from this template.
        POST /api/templates/{id}/instantiate/
        """
        template = self.get_object()

        serializer = TaskTemplateInstantiateSerializer(
            data=request.data,
            context={'request': request, 'template': template}
        )
        serializer.is_valid(raise_exception=True)
        
        # Assumes TaskTemplateInstantiateSerializer has a create_task method
        task = serializer.create_task(template=template)

        return Response(
            TaskDetailSerializer(task, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular templates."""
        templates = self.get_queryset().order_by('-usage_count')[:10]
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get templates grouped by category."""
        templates = self.get_queryset()

        # Group by category
        categories = {}
        for template in templates:
            category = template.category or 'Uncategorized'
            if category not in categories:
                categories[category] = []
            categories[category].append(
                TaskTemplateSerializer(template, context={'request': request}).data
            )

        return Response(categories)

class TaskAnalyticsView(APIView):
    def get(self, request):
        project_id = request.GET.get('project_id')
        project = Project.objects.get(id=project_id)
        
        report = generate_task_report(project)
        return Response(report)
        