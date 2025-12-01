"""
CollabSpace AI - Analytics Views
API endpoints for analytics and reporting functionality.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
import csv
from io import BytesIO
# Optional PDF export support
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .services import (
    WorkspaceAnalyticsService,
    ProjectAnalyticsService,
    TeamProductivityService
)
from .serializers import (
    WorkspaceAnalyticsQuerySerializer,
    ProjectAnalyticsQuerySerializer,
    BurndownChartQuerySerializer,
    VelocityQuerySerializer,
    TeamProductivityQuerySerializer,
    TimeTrackingReportQuerySerializer,
    MemberActivityQuerySerializer,
    TopPerformersQuerySerializer,
    WorkspaceMetricsOutputSerializer,
    ProjectProgressOutputSerializer,
    BurndownChartOutputSerializer,
    VelocityOutputSerializer,
    ProductivityOutputSerializer,
    TimeTrackingReportOutputSerializer
)
from apps.tasks.models import TimeEntry
from apps.core.permissions import IsWorkspaceMember, IsProjectMember


class WorkspaceAnalyticsView(APIView):
    """
    API endpoint for workspace-level analytics.
    
    GET /api/analytics/workspace/<uuid>/metrics/
    """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    
    def get(self, request, workspace_id):
        """Get comprehensive workspace metrics."""
        # Calculate metrics
        metrics = WorkspaceAnalyticsService.calculate_metrics(workspace_id)
        
        if 'error' in metrics:
            return Response(
                metrics,
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate and serialize output
        serializer = WorkspaceMetricsOutputSerializer(data=metrics)
        if serializer.is_valid():
            return Response(serializer.data)
        
        return Response(metrics)


class WorkspaceMemberActivityView(APIView):
    """
    API endpoint for workspace member activity.
    
    GET /api/analytics/workspace/<uuid>/member-activity/?days=30
    """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    
    def get(self, request, workspace_id):
        """Get member activity breakdown."""
        # Validate query parameters
        query_serializer = MemberActivityQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        
        days = query_serializer.validated_data.get('days', 30)
        
        # Get activity data
        activity_data = WorkspaceAnalyticsService.get_member_activity(
            workspace_id,
            days
        )
        
        return Response({
            'workspace_id': str(workspace_id),
            'period_days': days,
            'members': activity_data,
            'generated_at': timezone.now().isoformat()
        })


class ProjectAnalyticsView(APIView):
    """
    API endpoint for project-level analytics.
    
    GET /api/analytics/project/<uuid>/metrics/
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get(self, request, project_id):
        """Get comprehensive project metrics."""
        # Calculate progress
        progress = ProjectAnalyticsService.calculate_progress(project_id)
        
        if 'error' in progress:
            return Response(
                progress,
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate and serialize output
        serializer = ProjectProgressOutputSerializer(data=progress)
        if serializer.is_valid():
            return Response(serializer.data)
        
        return Response(progress)


class BurndownChartView(APIView):
    """
    API endpoint for burndown chart data.
    
    GET /api/analytics/project/<uuid>/burndown/?sprint_start=2024-01-01T00:00:00Z&sprint_end=2024-01-14T23:59:59Z
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get(self, request, project_id):
        """Generate burndown chart data for a sprint."""
        # Validate query parameters
        query_data = {
            'project_id': project_id,
            'sprint_start': request.query_params.get('sprint_start'),
            'sprint_end': request.query_params.get('sprint_end')
        }
        
        query_serializer = BurndownChartQuerySerializer(data=query_data)
        query_serializer.is_valid(raise_exception=True)
        
        validated = query_serializer.validated_data
        
        # Generate burndown data
        burndown = ProjectAnalyticsService.generate_burndown_chart(
            project_id=validated['project_id'],
            sprint_start=validated['sprint_start'],
            sprint_end=validated['sprint_end']
        )
        
        if 'error' in burndown:
            return Response(
                burndown,
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate and serialize output
        serializer = BurndownChartOutputSerializer(data=burndown)
        if serializer.is_valid():
            return Response(serializer.data)
        
        return Response(burndown)


class VelocityChartView(APIView):
    """
    API endpoint for team velocity data.
    
    GET /api/analytics/project/<uuid>/velocity/?num_sprints=5
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    
    def get(self, request, project_id):
        """Calculate team velocity over multiple sprints."""
        # Validate query parameters
        query_data = {
            'project_id': project_id,
            'num_sprints': request.query_params.get('num_sprints', 5)
        }
        
        query_serializer = VelocityQuerySerializer(data=query_data)
        query_serializer.is_valid(raise_exception=True)
        
        validated = query_serializer.validated_data
        
        # Calculate velocity
        velocity = ProjectAnalyticsService.calculate_velocity(
            project_id=validated['project_id'],
            num_sprints=validated['num_sprints']
        )
        
        if 'error' in velocity:
            return Response(
                velocity,
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate and serialize output
        serializer = VelocityOutputSerializer(data=velocity)
        if serializer.is_valid():
            return Response(serializer.data)
        
        return Response(velocity)


class TeamProductivityView(APIView):
    """
    API endpoint for team productivity metrics.
    
    GET /api/analytics/workspace/<uuid>/team-productivity/?user_id=xxx&period=month
    """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    
    def get(self, request, workspace_id):
        """Get team or individual productivity metrics."""
        # Validate query parameters
        query_data = dict(request.query_params)
        query_data['workspace_id'] = workspace_id
        
        query_serializer = TeamProductivityQuerySerializer(data=query_data)
        query_serializer.is_valid(raise_exception=True)
        
        validated = query_serializer.validated_data
        user_id = validated.get('user_id')
        
        if user_id:
            # Individual productivity
            productivity = TeamProductivityService.calculate_productivity_score(
                user_id=str(user_id),
                date_range=(validated['start_date'], validated['end_date'])
            )
            
            if 'error' in productivity:
                return Response(
                    productivity,
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = ProductivityOutputSerializer(data=productivity)
            if serializer.is_valid():
                return Response(serializer.data)
            
            return Response(productivity)
        else:
            # Top performers
            performers = TeamProductivityService.identify_top_performers(
                workspace_id=str(workspace_id),
                period=validated['period']
            )
            
            return Response({
                'workspace_id': str(workspace_id),
                'period': validated['period'],
                'top_performers': performers,
                'generated_at': timezone.now().isoformat()
            })


class TopPerformersView(APIView):
    """
    API endpoint for identifying top performers.
    
    GET /api/analytics/workspace/<uuid>/top-performers/?period=month&limit=10
    """
    permission_classes = [IsAuthenticated, IsWorkspaceMember]
    
    def get(self, request, workspace_id):
        """Get top performers in workspace."""
        # Validate query parameters
        query_data = {
            'workspace_id': workspace_id,
            'period': request.query_params.get('period', 'month'),
            'limit': request.query_params.get('limit', 10)
        }
        
        query_serializer = TopPerformersQuerySerializer(data=query_data)
        query_serializer.is_valid(raise_exception=True)
        
        validated = query_serializer.validated_data
        
        # Get top performers
        performers = TeamProductivityService.identify_top_performers(
            workspace_id=str(validated['workspace_id']),
            period=validated['period']
        )
        
        # Limit results
        performers = performers[:validated['limit']]
        
        return Response({
            'workspace_id': str(workspace_id),
            'period': validated['period'],
            'limit': validated['limit'],
            'top_performers': performers,
            'generated_at': timezone.now().isoformat()
        })


class TimeTrackingReportView(APIView):
    """
    API endpoint for time tracking reports with export options.
    
    GET /api/analytics/reports/time_tracking/?workspace_id=xxx&start_date=2024-01-01&end_date=2024-01-31
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generate time tracking report."""
        # Validate query parameters
        query_serializer = TimeTrackingReportQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        
        validated = query_serializer.validated_data
        
        # Build queryset
        queryset = TimeEntry.objects.all().select_related(
            'user', 'task', 'task__project'
        )
        
        # Apply filters
        if validated.get('workspace_id'):
            queryset = queryset.filter(
                task__project__workspace_id=validated['workspace_id']
            )
        
        if validated.get('project_id'):
            queryset = queryset.filter(
                task__project_id=validated['project_id']
            )
        
        if validated.get('user_id'):
            queryset = queryset.filter(user_id=validated['user_id'])
        
        # Date range filter
        queryset = queryset.filter(
            date__gte=validated['start_date'],
            date__lte=validated['end_date']
        )
        
        # Calculate summary
        summary = queryset.aggregate(
            total_hours=Sum('hours'),
            total_entries=Count('id')
        )
        
        # Group data
        group_by = validated['group_by']
        grouped_data = []
        
        if group_by == 'date':
            grouped_data = queryset.values('date').annotate(
                hours=Sum('hours'),
                entries=Count('id')
            ).order_by('date')
        elif group_by == 'user':
            grouped_data = queryset.values(
                'user__username', 'user__id'
            ).annotate(
                hours=Sum('hours'),
                entries=Count('id')
            ).order_by('-hours')
        elif group_by == 'project':
            grouped_data = queryset.values(
                'task__project__name', 'task__project__id'
            ).annotate(
                hours=Sum('hours'),
                entries=Count('id')
            ).order_by('-hours')
        elif group_by == 'task':
            grouped_data = queryset.values(
                'task__title', 'task__id'
            ).annotate(
                hours=Sum('hours'),
                entries=Count('id')
            ).order_by('-hours')
        
        # Prepare entries
        entries = []
        for entry in queryset:
            entries.append({
                'date': entry.date.isoformat(),
                'user': entry.user.username,
                'project': entry.task.project.name,
                'task': entry.task.title,
                'hours': float(entry.hours),
                'description': entry.description or ''
            })
        
        report_data = {
            'period': {
                'start': validated['start_date'].isoformat(),
                'end': validated['end_date'].isoformat()
            },
            'filters': {
                'workspace_id': str(validated.get('workspace_id')) if validated.get('workspace_id') else None,
                'project_id': str(validated.get('project_id')) if validated.get('project_id') else None,
                'user_id': str(validated.get('user_id')) if validated.get('user_id') else None,
                'group_by': group_by
            },
            'summary': {
                'total_hours': float(summary['total_hours'] or 0),
                'total_entries': summary['total_entries']
            },
            'entries': entries,
            'grouped_data': list(grouped_data),
            'generated_at': timezone.now().isoformat()
        }
        
        # Handle export format
        export_format = validated.get('export_format', 'json')
        
        if export_format == 'csv':
            return self.export_csv(report_data)
        elif export_format == 'pdf':
            if not REPORTLAB_AVAILABLE:
                return Response(
                    {'error': 'PDF export requires reportlab library. Please install it with: pip install reportlab'},
                    status=status.HTTP_501_NOT_IMPLEMENTED
                )
            return self.export_pdf(report_data)
        else:
            # Return JSON
            serializer = TimeTrackingReportOutputSerializer(data=report_data)
            if serializer.is_valid():
                return Response(serializer.data)
            return Response(report_data)
    
    def export_csv(self, report_data):
        """Export report as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="time_tracking_report_'
            f'{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        )
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Date', 'User', 'Project', 'Task', 'Hours', 'Description'
        ])
        
        # Write data
        for entry in report_data['entries']:
            writer.writerow([
                entry['date'],
                entry['user'],
                entry['project'],
                entry['task'],
                entry['hours'],
                entry['description']
            ])
        
        # Write summary
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Hours', report_data['summary']['total_hours']])
        writer.writerow(['Total Entries', report_data['summary']['total_entries']])
        
        return response
    
    def export_pdf(self, report_data):
        """Export report as PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(
            '<b>Time Tracking Report</b>',
            styles['Title']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Period
        period_text = (
            f"Period: {report_data['period']['start']} to "
            f"{report_data['period']['end']}"
        )
        elements.append(Paragraph(period_text, styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Summary
        summary_text = (
            f"<b>Total Hours:</b> {report_data['summary']['total_hours']}<br/>"
            f"<b>Total Entries:</b> {report_data['summary']['total_entries']}"
        )
        elements.append(Paragraph(summary_text, styles['Normal']))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Table data
        table_data = [['Date', 'User', 'Project', 'Task', 'Hours']]
        for entry in report_data['entries'][:100]:  # Limit to 100 for PDF
            table_data.append([
                entry['date'],
                entry['user'][:20],  # Truncate long names
                entry['project'][:20],
                entry['task'][:30],
                str(entry['hours'])
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 1.5*inch, 2*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Return response
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="time_tracking_report_'
            f'{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        )
        
        return response

class TeamVelocityView(APIView):
    """
    API endpoint for team velocity data (by team ID).
    
    GET /api/analytics/team/<slug>/velocity/
    """
    permission_classes = [IsAuthenticated, IsWorkspaceMember] # Adjust permissions as needed
    
    def get(self, request, team_id):
        # Implementation for calculating team velocity goes here
        # (This is where you would call a new service method)
        return Response({'message': f'Calculating velocity for team: {team_id}'})