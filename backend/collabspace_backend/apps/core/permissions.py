from typing import Optional
import logging

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated

logger = logging.getLogger(__name__)


def _get_model(name: str):
    """
    Helper to lazily import model by name.
    Expects model names like 'workspaces.Workspace' or 'core.Workspace' depending on your project.
    Adjust module label as needed.
    """
    try:
        app_label, model_name = name.split(".")
        return apps.get_model(app_label, model_name)
    except Exception:
        # Fallback: try common app labels
        for try_label in ("workspaces", "projects", "tasks", "core", "app"):
            try:
                return apps.get_model(try_label, name)
            except Exception:
                continue
    raise LookupError(f"Model '{name}' not found")


# Attempt to get commonly used models (adjust if your app labels differ)
try:
    Workspace = _get_model("workspaces.Workspace")
except Exception:
    Workspace = None
try:
    WorkspaceMember = _get_model("workspaces.WorkspaceMember")
except Exception:
    WorkspaceMember = None
try:
    Project = _get_model("projects.Project")
except Exception:
    Project = None
try:
    ProjectMember = _get_model("projects.ProjectMember")
except Exception:
    ProjectMember = None
try:
    Task = _get_model("tasks.Task")
except Exception:
    Task = None


class IsWorkspaceMember(BasePermission):
    """
    Allow access only to users who are a member of the workspace.
    Expects view.kwargs['workspace_id'] or request.data['workspace'] (id).
    """

    message = "User is not a member of this workspace."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace_id = getattr(view, "kwargs", {}).get("workspace_id") or request.data.get("workspace")
        if not workspace_id:
            # allow safe methods if resource is public? Deny by default
            logger.debug("IsWorkspaceMember: no workspace_id present in request/view")
            return False
        if WorkspaceMember is None:
            logger.warning("WorkspaceMember model not available")
            return False
        try:
            return WorkspaceMember.objects.filter(user=request.user, workspace_id=workspace_id).exists()
        except Exception as exc:
            logger.exception("Error checking workspace membership: %s", exc)
            return False


class IsWorkspaceOwner(BasePermission):
    """
    Allow only if user is workspace.owner
    """

    message = "User is not the owner of this workspace."

    def has_object_permission(self, request, view, obj):
        # If object is a workspace itself:
        if hasattr(obj, "owner_id"):
            return obj.owner_id == getattr(request.user, "id", None)
        # Otherwise, try to get workspace attribute:
        workspace = getattr(obj, "workspace", None)
        if workspace is not None:
            return getattr(workspace, "owner_id", None) == getattr(request.user, "id", None)
        return False


class IsWorkspaceAdmin(BasePermission):
    """
    Allow if user has an admin role in WorkspaceMember.
    Expect WorkspaceMember.role to contain 'admin' or similar.
    """

    message = "User must be a workspace admin."

    def _is_admin(self, user, workspace_id) -> bool:
        if WorkspaceMember is None:
            logger.warning("WorkspaceMember model not available")
            return False
        try:
            membership = WorkspaceMember.objects.filter(user=user, workspace_id=workspace_id).first()
            if not membership:
                return False
            role = getattr(membership, "role", None)
            # Accept both string role flags and boolean admin flags
            if isinstance(role, str):
                return role.lower() in ("admin", "owner", "maintainer")
            return getattr(membership, "is_admin", False) or getattr(membership, "is_owner", False)
        except Exception:
            logger.exception("Error checking workspace admin")
            return False

    def has_permission(self, request, view):
        workspace_id = getattr(view, "kwargs", {}).get("workspace_id") or request.data.get("workspace")
        if not workspace_id:
            return False
        return self._is_admin(request.user, workspace_id)


class IsProjectMember(BasePermission):
    """
    Permission to check if user is a member of the project or workspace.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is a member of the project or the workspace.
        For Task objects, obj is the task, so we check task.project.
        For Project objects, obj is the project itself.
        """
        # Get the project
        if hasattr(obj, 'project'):
            # obj is a Task or related object
            project = obj.project
        else:
            # obj is a Project
            project = obj
        
        # Check if user is a project member
        if project.is_member(request.user):
            return True
        
        # Check if user is a workspace member (important!)
        if project.workspace.is_member(request.user):
            return True
        
        # Check if user is the project owner
        if project.owner == request.user:
            return True
        
        return False

class IsProjectOwner(BasePermission):
    """
    Allow only if user is project.owner
    """

    message = "User is not the owner of this project."

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "owner_id"):
            return obj.owner_id == getattr(request.user, "id", None)
        project = getattr(obj, "project", None)
        if project is not None:
            return getattr(project, "owner_id", None) == getattr(request.user, "id", None)
        return False


class IsTaskAssignee(BasePermission):
    """
    Allow only if user is assignee of the task
    """

    message = "User is not assigned to this task."

    def has_object_permission(self, request, view, obj):
        # obj is expected to be a Task instance
        if hasattr(obj, "assigned_to_id"):
            return getattr(request.user, "id", None) == obj.assigned_to_id
        assignee = getattr(obj, "assigned_to", None)
        if assignee is not None:
            return assignee == request.user
        return False


class IsResourceOwner(BasePermission):
    """
    Generic owner check for resources that have 'owner' or 'created_by' attribute.
    """

    message = "User does not own this resource."

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "owner", None) or getattr(obj, "created_by", None)
        if owner is None:
            # allow read for owners? default deny
            return False
        if hasattr(owner, "id"):
            return owner.id == getattr(request.user, "id", None)
        return owner == request.user


class HasWorkspaceAccess(BasePermission):
    """
    Checks workspace existence and plan limits. Real plan-check logic must be implemented
    in `check_workspace_plan_limits` below.
    """

    message = "Workspace access denied or plan limits exceeded."

    def check_workspace_plan_limits(self, workspace):
        """
        Placeholder for plan/limits enforcement. Replace with real logic that inspects
        workspace.plan / workspace.subscription / feature flags.
        Should return True if access is allowed.
        """
        # Default: allow
        return True

    def has_permission(self, request, view):
        workspace_id = getattr(view, "kwargs", {}).get("workspace_id") or request.data.get("workspace")
        if not workspace_id:
            logger.debug("HasWorkspaceAccess: no workspace id")
            return False
        if Workspace is None:
            logger.warning("Workspace model not available")
            return False
        try:
            workspace = Workspace.objects.filter(pk=workspace_id).first()
            if not workspace:
                return False
            # Optionally check membership too
            if WorkspaceMember:
                if not WorkspaceMember.objects.filter(user=request.user, workspace=workspace).exists():
                    return False
            return self.check_workspace_plan_limits(workspace)
        except Exception:
            logger.exception("Error checking workspace access")
            return False


class HasProjectAccess(BasePermission):
    """
    Checks project visibility (public/private) and membership.
    If project is public, allow read-only access.
    """

    message = "Project access denied."

    def has_permission(self, request, view):
        project_id = getattr(view, "kwargs", {}).get("project_id") or request.data.get("project")
        if not project_id:
            return False
        if Project is None:
            logger.warning("Project model not available")
            return False
        try:
            project = Project.objects.filter(pk=project_id).first()
            if not project:
                return False
            # Public project: allow safe methods
            if getattr(project, "is_public", False) and request.method in SAFE_METHODS:
                return True
            # Else require membership
            if ProjectMember:
                return ProjectMember.objects.filter(user=request.user, project=project).exists()
            # Fallback to workspace membership
            workspace = getattr(project, "workspace", None)
            if workspace and WorkspaceMember:
                return WorkspaceMember.objects.filter(user=request.user, workspace=workspace).exists()
            return False
        except Exception:
            logger.exception("Error checking project access")
            return False


class CanModifyResource(BasePermission):
    """
    Composite permission: allow modification when user is resource owner, workspace admin, or project owner.
    """

    message = "You do not have permission to modify this resource."

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # Owner
        if IsResourceOwner().has_object_permission(request, view, obj):
            return True
        # Workspace owner or admin
        workspace = getattr(obj, "workspace", None)
        if workspace:
            if workspace.owner_id == getattr(user, "id", None):
                return True
            if WorkspaceMember and WorkspaceMember.objects.filter(user=user, workspace=workspace, role__in=["admin", "owner"]).exists():
                return True
        # Project owner
        project = getattr(obj, "project", None)
        if project:
            if getattr(project, "owner_id", None) == getattr(user, "id", None):
                return True
            if ProjectMember and ProjectMember.objects.filter(user=user, project=project, role__in=["owner", "admin"]).exists():
                return True

        return False
