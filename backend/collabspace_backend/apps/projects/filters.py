import django_filters
from .models import Project


class ProjectFilter(django_filters.FilterSet):
    """
    FilterSet for the Project model.
    Allows filtering by status, priority, workspace ID, and date range.
    """
    
    # Filter by specific choices
    status = django_filters.ChoiceFilter(
        choices=Project.status.field.choices,
        lookup_expr='exact',
        label='Project Status'
    )
    priority = django_filters.ChoiceFilter(
        choices=Project.priority.field.choices,
        lookup_expr='exact',
        label='Project Priority'
    )

    # Filter by workspace (using ID for API consistency)
    workspace = django_filters.UUIDFilter(
        field_name='workspace__id',
        lookup_expr='exact',
        label='Workspace ID'
    )
    
    # Filter by date range (e.g., projects starting after a certain date)
    start_date_after = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='gte',
        label='Start Date (After)'
    )
    
    # Filter by ownership
    owner = django_filters.UUIDFilter(
        field_name='owner__id',
        lookup_expr='exact',
        label='Owner ID'
    )

    class Meta:
        model = Project
        fields = [
            'status',
            'priority',
            'workspace',
            'owner',
            'is_public',
        ]