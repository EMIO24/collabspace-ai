from typing import Optional

from django.apps import apps
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
import logging

logger = logging.getLogger(__name__)

# Models are retrieved via apps.get_model to avoid circular imports
Workspace = apps.get_model("workspaces", "Workspace")
WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")


def _get_workspace_from_view(view) -> Optional[Workspace]:
    """
    Helper: try to get workspace instance from view attributes.
    Many viewsets use lookup kwarg names like 'workspace_id' or 'pk'.
    """
    # If the view already set .get_object() or .kwargs we can inspect kwargs
    try:
        kwargs = getattr(view, "kwargs", None) or {}
        workspace_id = kwargs.get("workspace_id") or kwargs.get("pk")
        if workspace_id:
            return Workspace.objects.filter(pk=workspace_id).first()
    except Exception:
        logger.debug("Unable to fetch workspace from view kwargs", exc_info=True)
    return None


def _get_member_role(user, workspace: Workspace) -> Optional[str]:
    """Return member role string for user in workspace or None."""
    if user is None or workspace is None or not user.is_authenticated:
        return None
    try:
        membership = WorkspaceMember.objects.filter(
            workspace=workspace, user=user, is_active=True
        ).first()
        return getattr(membership, "role", None) if membership else None
    except Exception:
        logger.exception("Error looking up membership")
        return None


class IsWorkspaceOwner(permissions.BasePermission):
    """
    Allow access only to the workspace owner.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        # For non-object level checks allow, object check below
        return True

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # obj may be a Workspace instance
        workspace = obj if getattr(obj, "owner_id", None) else _get_workspace_from_view(view)
        if workspace is None:
            return False
        return workspace.owner_id == request.user.id


class IsWorkspaceAdmin(permissions.BasePermission):
    """
    Allow access to workspace admins and owner.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        workspace = obj if getattr(obj, "id", None) else _get_workspace_from_view(view)
        if workspace is None:
            return False
        if workspace.owner_id == request.user.id:
            return True
        role = _get_member_role(request.user, workspace)
        return role in ("admin", "maintainer")


class IsWorkspaceMember(permissions.BasePermission):
    """
    Allow access if the user is a member (including owner).
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        workspace = obj if getattr(obj, "id", None) else _get_workspace_from_view(view)
        if workspace is None:
            return False
        if workspace.owner_id == request.user.id:
            return True
        role = _get_member_role(request.user, workspace)
        return role is not None


class CanManageMembers(permissions.BasePermission):
    """
    Allow members with permission to manage members (owner or admins).
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # Owner or admin can manage members
        owner_ok = getattr(obj, "owner_id", None) == request.user.id
        if owner_ok:
            return True
        role = _get_member_role(request.user, obj if getattr(obj, "id", None) else _get_workspace_from_view(view))
        return role in ("admin", "maintainer")


class CanManageSettings(permissions.BasePermission):
    """
    Allow only owner or specific high-level admins to manage workspace settings.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # Strict: only owner or 'owner-delegate' style role
        workspace = obj if getattr(obj, "id", None) else _get_workspace_from_view(view)
        if not workspace:
            return False
        if workspace.owner_id == request.user.id:
            return True
        role = _get_member_role(request.user, workspace)
        return role == "owner-delegate"


class CanInviteMembers(permissions.BasePermission):
    """
    Allow members who may invite (owner, admin, or members with invite flag).
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        workspace = obj if getattr(obj, "id", None) else _get_workspace_from_view(view)
        if not workspace:
            return False
        if workspace.owner_id == request.user.id:
            return True
        role = _get_member_role(request.user, workspace)
        if role in ("admin", "maintainer"):
            return True
        # Optionally, WorkspaceMember model may have can_invite boolean
        try:
            membership = WorkspaceMember.objects.filter(
                workspace=workspace, user=request.user, is_active=True
            ).first()
            if membership and getattr(membership, "can_invite", False):
                return True
        except Exception:
            logger.exception("Error checking invite capability")
        return False


class CanRemoveMembers(permissions.BasePermission):
    """
    Owner and admins can remove other members; members cannot remove owner.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        workspace = obj if getattr(obj, "id", None) else _get_workspace_from_view(view)
        if not workspace:
            return False
        if workspace.owner_id == request.user.id:
            return True
        role = _get_member_role(request.user, workspace)
        return role == "admin"
