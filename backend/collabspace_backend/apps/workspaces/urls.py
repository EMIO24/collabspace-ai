from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import the viewsets / views used by routes
from .views import (
    WorkspaceViewSet,
    WorkspaceMemberViewSet,
    WorkspaceInvitationViewSet,
    WorkspaceStatsView,
    WorkspaceActivityView,
    WorkspaceSearchView,
)

app_name = "workspaces"

router = DefaultRouter()
# Register the primary Workspace viewset at /api/workspaces/ (router root)
router.register("", WorkspaceViewSet, basename="workspace")

urlpatterns = [
    # Main workspace routes (list, retrieve, create, update, destroy)
    path("", include(router.urls)),

    # Member management (scoped to a workspace UUID)
    path(
        "<uuid:workspace_id>/members/",
        WorkspaceMemberViewSet.as_view({"get": "list", "post": "create"}),
        name="workspace-members-list-create",
    ),
    path(
        "<uuid:workspace_id>/members/<uuid:user_id>/",
        WorkspaceMemberViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="workspace-members-detail",
    ),

    # Invitations
    path(
        "<uuid:workspace_id>/invitations/",
        WorkspaceInvitationViewSet.as_view({"get": "list", "post": "create"}),
        name="workspace-invitations-list-create",
    ),
    path(
        "<uuid:workspace_id>/invitations/<int:invitation_id>/",
        WorkspaceInvitationViewSet.as_view({"delete": "destroy"}),
        name="workspace-invitations-destroy",
    ),
    path(
        "invitations/accept/",
        WorkspaceInvitationViewSet.as_view({"post": "accept_invitation"}),
        name="workspace-invitations-accept",
    ),
    path(
        "invitations/decline/",
        WorkspaceInvitationViewSet.as_view({"post": "decline_invitation"}),
        name="workspace-invitations-decline",
    ),

    # Stats and activity
    path(
        "<uuid:workspace_id>/stats/",
        WorkspaceStatsView.as_view(),
        name="workspace-stats",
    ),
    path(
        "<uuid:workspace_id>/activity/",
        WorkspaceActivityView.as_view(),
        name="workspace-activity",
    ),

    # Search
    path("search/", WorkspaceSearchView.as_view(), name="workspace-search"),
]
