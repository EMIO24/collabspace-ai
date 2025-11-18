import json
from datetime import datetime, timedelta

# Mocking Django Rest Framework imports
class MockRequest:
    def __init__(self, params=None):
        self.query_params = params if params is not None else {}
        self.method = 'GET'

class MockResponse:
    def __init__(self, data=None, status=200, content_type='application/json'):
        self.data = data
        self.status_code = status
        self.content_type = content_type
        
        # Simulate Django's HttpResponse setup for file download
        if content_type != 'application/json':
             self.headers = {
                 'Content-Disposition': f'attachment; filename="{data.get("filename", "report.csv")}"'
             }
        else:
             self.headers = {}
             
    def json(self):
        if self.content_type == 'application/json':
            return self.data
        return {'error': 'Not a JSON response'}

# Import local modules
from .services import AnalyticsService
from .serializers import (
    WorkspaceAnalyticsSerializer, ProjectAnalyticsSerializer,
    TeamProductivitySerializer, BurndownChartSerializer, VelocityChartSerializer
)

service = AnalyticsService()

# --- Base View Mock ---
class APIViewMock:
    """Mocking a DRF APIView base class for demonstration."""
    def dispatch(self, request):
        if request.method == 'GET':
            return self.get(request)
        return MockResponse(data={'detail': 'Method not allowed'}, status=405)

# --- Analytics Views ---

class WorkspaceAnalyticsView(APIViewMock):
    """API endpoint for fetching workspace-wide analytics."""
    def get(self, request: MockRequest, workspace_id: int):
        metrics = service.calculate_workspace_metrics(workspace_id)
        serializer = WorkspaceAnalyticsSerializer(metrics)
        return MockResponse(data=serializer.to_representation(metrics), status=200)

class ProjectAnalyticsView(APIViewMock):
    """API endpoint for fetching project-specific analytics."""
    def get(self, request: MockRequest, project_id: int):
        metrics = service.calculate_project_metrics(project_id)
        serializer = ProjectAnalyticsSerializer(metrics)
        return MockResponse(data=serializer.to_representation(metrics), status=200)

class TeamProductivityView(APIViewMock):
    """API endpoint for fetching team member productivity."""
    def get(self, request: MockRequest, workspace_id: int):
        metrics = service.calculate_team_productivity(workspace_id)
        # Serializers handle list data implicitly in DRF
        serializer = TeamProductivitySerializer(metrics)
        return MockResponse(data=serializer.to_representation(metrics), status=200)

# --- Chart Views ---

class BurndownChartView(APIViewMock):
    """API endpoint for burndown chart data."""
    def get(self, request: MockRequest, project_id: int):
        chart_data = service.generate_burndown_chart(project_id)
        serializer = BurndownChartSerializer(chart_data)
        return MockResponse(data=serializer.to_representation(chart_data), status=200)

class VelocityChartView(APIViewMock):
    """API endpoint for velocity chart data."""
    def get(self, request: MockRequest, team_id: str):
        chart_data = service.generate_velocity_chart(team_id)
        serializer = VelocityChartSerializer(chart_data)
        return MockResponse(data=serializer.to_representation(chart_data), status=200)

# --- Report View with Export ---

class TimeTrackingReportView(APIViewMock):
    """
    API endpoint for detailed time tracking reports with export functionality.
    Access via /reports/time_tracking/?user_id=X&format=csv
    """
    def get(self, request: MockRequest):
        user_id = request.query_params.get('user_id')
        format = request.query_params.get('format', 'json').lower()
        
        # Default date range: last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # NOTE: A real implementation would parse date params here, e.g.,
        # start_date = datetime.fromisoformat(request.query_params.get('start_date'))
        # end_date = datetime.fromisoformat(request.query_params.get('end_date'))
        
        if not user_id:
            return MockResponse(data={'error': 'user_id parameter is required.'}, status=400)

        # 1. Generate Report Data
        # For simplicity, we only have the CSV generation function in the service layer
        csv_data = service.generate_time_tracking_report_csv(user_id, start_date, end_date)
        
        # 2. Handle Export Format
        if format == 'csv':
            # In a real DRF app, this uses HttpResponse with 'text/csv' and Content-Disposition header
            return MockResponse(
                data={
                    'filename': f'time_tracking_report_{user_id}_{end_date.strftime("%Y%m%d")}.csv',
                    'content': csv_data
                },
                status=200,
                content_type='text/csv'
            )
        elif format == 'pdf':
            # Mock PDF generation
            # In a real app, you would use a library like ReportLab or WeasyPrint
            return MockResponse(
                data={'detail': 'PDF export not yet implemented. Use CSV format.'},
                status=501
            )
        else: # Default JSON response (we send the CSV content as a string inside JSON)
            # A real JSON response would first convert the CSV data back to structured JSON list/dict
            return MockResponse(data={
                'user_id': user_id,
                'report_period': f'{start_date.date()} to {end_date.date()}',
                'csv_content_preview': csv_data
            }, status=200)