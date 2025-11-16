import django_filters
from django.apps import apps
from django_filters import rest_framework as filters

Workspace = apps.get_model("workspaces", "Workspace")
WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")


class WorkspaceFilter(filters.FilterSet):
    """
    FilterSet for Workspace list queries.
    - name: icontains
    - owner: exact match by id or username
    - plan_type: exact
    - is_public: boolean
    - created_after / created_before: date range
    """

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    owner = django_filters.CharFilter(method="filter_by_owner")
    plan_type = django_filters.CharFilter(field_name="plan_type", lookup_expr="exact")
    is_public = django_filters.BooleanFilter(field_name="is_public")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Workspace
        fields = ["name", "owner", "plan_type", "is_public", "created_after", "created_before"]

    def filter_by_owner(self, queryset, name, value):
        """
        Owner filter supports either user PK, username or email.
        """
        User = apps.get_model("auth", "User")
        # try pk
        qs = queryset
        try:
            # numeric or UUID pk support
            qs = qs.filter(owner__pk=value)
            if qs.exists():
                return qs
        except Exception:
            pass

        # username or email fallback
        return queryset.filter(owner__username__iexact=value) | queryset.filter(owner__email__iexact=value)


class WorkspaceMemberFilter(filters.FilterSet):
    """
    FilterSet for workspace members.
    - role
    - joined_after, joined_before (on joined_at / created_at)
    """

    role = django_filters.CharFilter(field_name="role", lookup_expr="exact")
    joined_after = django_filters.DateTimeFilter(field_name="joined_at", lookup_expr="gte")
    joined_before = django_filters.DateTimeFilter(field_name="joined_at", lookup_expr="lte")

    class Meta:
        model = WorkspaceMember
        fields = ["role", "joined_after", "joined_before"]
