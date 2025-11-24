from collections import defaultdict
from datetime import timedelta
import uuid
from typing import Any, Dict, Optional

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError  
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


try:
    from .serializers import (
        WorkspaceListSerializer,
        WorkspaceDetailSerializer,
        WorkspaceCreateSerializer,
        WorkspaceUpdateSerializer,
        WorkspaceMemberSerializer,
        AddMemberSerializer,  
        WorkspaceInvitationSerializer,
        SendInvitationSerializer,  
        WorkspaceStatsReadSerializer, 
        WorkspaceActivitySerializer,
        WorkspaceSearchSerializer,
    )


    WorkspaceMemberCreateSerializer = AddMemberSerializer
    WorkspaceInvitationCreateSerializer = SendInvitationSerializer
    WorkspaceStatsSerializer = WorkspaceStatsReadSerializer
    WorkspaceActivitySerializer = WorkspaceActivitySerializer 
    WorkspaceSearchSerializer = WorkspaceSearchSerializer  
except ImportError as e:
    print(f"Serializer import error: {e}")
    raise

# -----------------------------
# Helper permissions
# -----------------------------

class IsWorkspaceOwner(BasePermission):
    """Allow access only to workspace owners."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # Expect workspace to have .owner attribute
        return hasattr(obj, "owner") and obj.owner_id == request.user.id


class IsWorkspaceAdminOrOwner(BasePermission):
    """Allow access to workspace owner or admins (workspace membership role)."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if hasattr(obj, "owner") and obj.owner_id == request.user.id:
            return True
        # check membership role
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        try:
            membership = WorkspaceMember.objects.filter(workspace=obj, user=request.user).first()
            if not membership:
                return False
            return getattr(membership, "role", "member") in ("owner", "admin")
        except Exception:
            return False


class IsWorkspaceMember(BasePermission):
    """Allow access to workspace members (read-only for guests)."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        return WorkspaceMember.objects.filter(workspace=obj, user=request.user).exists()


# -----------------------------
# Pagination
# -----------------------------

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200


# -----------------------------
# WorkspaceViewSet
# -----------------------------

class WorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Workspaces.

    Endpoints:
    - list: filters by memberships, search, ordering and pagination
    - create: create workspace, set owner, create owner membership
    - retrieve: membership required
    - update: owner/admin only
    - destroy: owner only -> soft delete + archive projects

    Custom actions:
    - archive_workspace
    - restore_workspace
    - duplicate_workspace
    - leave_workspace
    - transfer_ownership
    """

    lookup_field = "id"
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = ("name", "created_at", "member_count")
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        Workspace = apps.get_model("workspaces", "Workspace")
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        # Return workspaces where the user is a member (exclude archived/deleted unless owner)
        member_workspace_ids = WorkspaceMember.objects.filter(user=self.request.user).values_list("workspace_id", flat=True)
        qs = Workspace.objects.filter(id__in=member_workspace_ids)
        # Optional: filter out soft-deleted
        if hasattr(Workspace, "is_archived"):
            qs = qs.filter(is_archived=False)
        if hasattr(Workspace, "is_deleted"):
            qs = qs.filter(is_deleted=False)
        # annotate member_count if field missing
        if not hasattr(Workspace._meta.model, "member_count"):
            qs = qs.annotate(member_count=Count("members"))
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return WorkspaceListSerializer or WorkspaceDetailSerializer
        if self.action in ("create",):
            return WorkspaceCreateSerializer or WorkspaceDetailSerializer
        if self.action in ("update", "partial_update"):
            return WorkspaceUpdateSerializer or WorkspaceDetailSerializer
        return WorkspaceDetailSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List workspaces the user is a member of. Supports search and ordering."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a workspace and make the request user the owner."""
        Workspace = apps.get_model("workspaces", "Workspace")
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # create workspace
        workspace = Workspace.objects.create(owner=request.user, **data)
        
        # create owner membership with is_active=True
        membership, created = WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            user=request.user,
            defaults={'role': 'owner', 'is_active': True}
        )
        
        # If membership existed but was inactive, reactivate it
        if not created and not membership.is_active:
            membership.is_active = True
            membership.role = 'owner'
            membership.save()
        
        # Update workspace counts
        workspace.update_counts()
        
        try:
            if hasattr(workspace, "send_creation_confirmation"):
                workspace.send_creation_confirmation(request.user)
        except Exception:
            pass
        
        out_serializer = WorkspaceDetailSerializer(workspace, context={'request': request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve detailed workspace info. Membership is required."""
        workspace = self.get_object()
        # membership check
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
            return Response({"detail": "Not a member of this workspace."}, status=status.HTTP_403_FORBIDDEN)
        serializer = WorkspaceDetailSerializer(workspace)
        return Response(serializer.data)

    @transaction.atomic
    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update workspace. Only owner or admin may update. Handles slug regeneration if name changed."""
        partial = kwargs.pop("partial", False)
        workspace = self.get_object()
        # permission check
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "You do not have permission to update this workspace."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(workspace, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        old_name = getattr(workspace, "name", None)
        workspace = serializer.save()
        # handle slug regeneration
        if old_name and old_name != getattr(workspace, "name", None) and hasattr(workspace, "regenerate_slug"):
            try:
                workspace.regenerate_slug()
                workspace.save()
            except Exception:
                pass
        out_serializer = WorkspaceDetailSerializer(workspace)
        return Response(out_serializer.data)

    @transaction.atomic
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Soft-delete a workspace. Only owner may perform deletion. Archive projects."""
        workspace = self.get_object()
        if not IsWorkspaceOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "You must be the workspace owner to delete it."}, status=status.HTTP_403_FORBIDDEN)
        
        # soft delete flag
        if hasattr(workspace, "is_deleted"):
            workspace.is_deleted = True
            workspace.deleted_at = timezone.now()
            workspace.save()
        else:
            workspace.delete()
        
        # archive projects if model supports it
        Project = apps.get_model("projects", "Project") if apps.is_installed("apps.projects") or apps.is_installed("projects") else None
        if Project:
            try:
                # Check if Project model has is_archived field
                project_field_names = [f.name for f in Project._meta.get_fields()]
                if 'is_archived' in project_field_names:
                    Project.objects.filter(workspace=workspace).update(is_archived=True)
                # Otherwise, do nothing - projects will remain but workspace is deleted
            except Exception as e:
                # Log the error but don't fail the workspace deletion
                pass
        
        return Response(status=status.HTTP_204_NO_CONTENT)


    # -----------------------------
    # Custom actions
    # -----------------------------
    @action(detail=True, methods=["post"])
    def archive_workspace(self, request: Request, id: str = None) -> Response:
        """Archive the workspace (admin/owner only)."""
        workspace = self.get_object()
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        if hasattr(workspace, "is_archived"):
            workspace.is_archived = True
            workspace.archived_at = timezone.now()
            workspace.save()
        else:
            # fallback: mark deleted
            workspace.delete()
        
        # archive projects
        Project = apps.get_model("projects", "Project") if apps.is_installed("apps.projects") or apps.is_installed("projects") else None
        if Project:
            try:
                # Check if Project model has is_archived field
                project_field_names = [f.name for f in Project._meta.get_fields()]
                if 'is_archived' in project_field_names:
                    Project.objects.filter(workspace=workspace).update(is_archived=True)
            except Exception:
                pass
        
        return Response({"detail": "Workspace archived."})


    @action(detail=True, methods=["post"])  # /{id}/restore_workspace/
    def restore_workspace(self, request: Request, id: str = None) -> Response:
        """Restore an archived workspace (owner only)."""
        workspace = self.get_object()
        if not IsWorkspaceOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        if hasattr(workspace, "is_archived"):
            workspace.is_archived = False
            workspace.archived_at = None
            workspace.save()
            return Response({"detail": "Workspace restored."})
        return Response({"detail": "Workspace cannot be restored."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])  # /{id}/duplicate_workspace/
    def duplicate_workspace(self, request: Request, id: str = None) -> Response:
        """Duplicate a workspace (owner/admin). Deep-copy projects optionally.

        Note: this is an expensive operation; implement as background job for large workspaces.
        Here we make a best-effort synchronous duplicate.
        """
        workspace = self.get_object()
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        Workspace = apps.get_model("workspaces", "Workspace")
        # shallow copy fields
        dup = Workspace.objects.create(
            name=f"{workspace.name} (copy)",
            description=getattr(workspace, "description", ""),
            owner=request.user,
            is_public=getattr(workspace, "is_public", False),
        )
        # duplicate members: add request.user as owner only
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        WorkspaceMember.objects.create(workspace=dup, user=request.user, role="owner")
        # TODO: duplicate projects/tasks if desired
        out = WorkspaceDetailSerializer(dup)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])  # /{id}/leave_workspace/
    def leave_workspace(self, request: Request, id: str = None) -> Response:
        """Allow a member to leave the workspace. Owners cannot leave without transfer."""
        workspace = self.get_object()
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        membership = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).first()
        if not membership:
            return Response({"detail": "Not a member."}, status=status.HTTP_400_BAD_REQUEST)
        if getattr(membership, "role", "member") == "owner":
            return Response({"detail": "Owner cannot leave workspace. Transfer ownership first."}, status=status.HTTP_400_BAD_REQUEST)
        membership.delete()
        return Response({"detail": "Left workspace."})

    @action(detail=True, methods=["post"])  # /{id}/transfer_ownership/
    def transfer_ownership(self, request: Request, id: str = None) -> Response:
        """Transfer ownership to another member. Only current owner may perform this."""
        workspace = self.get_object()
        if not IsWorkspaceOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Only owner can transfer ownership."}, status=status.HTTP_403_FORBIDDEN)
        target_user_id = request.data.get("user_id")
        if not target_user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        User = apps.get_model(settings.AUTH_USER_MODEL.split(".")[0], settings.AUTH_USER_MODEL.split(".")[1]) if "." in settings.AUTH_USER_MODEL else apps.get_model(settings.AUTH_USER_MODEL)
        try:
            new_owner = User.objects.get(id=target_user_id)
        except Exception:
            return Response({"detail": "Target user not found."}, status=status.HTTP_404_NOT_FOUND)
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        membership = WorkspaceMember.objects.filter(workspace=workspace, user=new_owner).first()
        if not membership:
            return Response({"detail": "Target user must be a member."}, status=status.HTTP_400_BAD_REQUEST)
        # perform transfer
        workspace.owner = new_owner
        workspace.save()
        # update roles
        owner_membership = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).first()
        if owner_membership:
            owner_membership.role = "admin"
            owner_membership.save()
        membership.role = "owner"
        membership.save()
        return Response({"detail": "Ownership transferred."})


# -----------------------------
# WorkspaceMemberViewSet
# -----------------------------

class WorkspaceMemberViewSet(viewsets.ViewSet):
    """Manage workspace members. URL: /api/workspaces/{workspace_id}/members/"""

    permission_classes = (IsAuthenticated,)
    lookup_field = "user_id"

    def _get_workspace(self, workspace_id: str):
        Workspace = apps.get_model("workspaces", "Workspace")
        return get_object_or_404(Workspace, id=workspace_id)

    def list(self, request: Request, workspace_id: str = None) -> Response:
        """List members for a workspace. Supports filtering by role and searching by name/email."""
        workspace = self._get_workspace(workspace_id)
        # permission: must be a member to view
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user, is_active=True).exists():
            return Response({"detail": "Not a workspace member."}, status=status.HTTP_403_FORBIDDEN)
        
        qs = WorkspaceMember.objects.filter(workspace=workspace, is_active=True)
        role = request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(user__email__icontains=q) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q))
        
        serializer = WorkspaceMemberSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request: Request, workspace_id: str = None) -> Response:
        """Add a member to the workspace. Requires admin/owner privilege."""
        workspace = self._get_workspace(workspace_id)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        # Pass workspace in context - THIS IS THE KEY FIX
        serializer = WorkspaceMemberCreateSerializer(
            data=request.data,
            context={'workspace': workspace, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # The serializer.save() handles everything
        result = serializer.save()
        
        # Check if result is an invitation or membership
        WorkspaceInvitation = apps.get_model("workspaces", "WorkspaceInvitation")
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        
        if isinstance(result, WorkspaceInvitation):
            # An invitation was created
            try:
                result.send_invitation_email()
            except Exception:
                pass
            out = WorkspaceInvitationSerializer(result, context={'request': request})
            return Response(out.data, status=status.HTTP_201_CREATED)
        else:
            # Membership was created
            # Update workspace counts
            workspace.update_counts()
            out = WorkspaceMemberSerializer(result, context={'request': request})
            return Response(out.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, workspace_id: str = None, user_id: str = None) -> Response:
        workspace = self._get_workspace(workspace_id)
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        membership = get_object_or_404(WorkspaceMember, workspace=workspace, user__id=user_id, is_active=True)
        
        # permissions: must be member
        if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user, is_active=True).exists():
            return Response({"detail": "Not a member."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = WorkspaceMemberSerializer(membership, context={'request': request})
        return Response(serializer.data)

    def update(self, request: Request, workspace_id: str = None, user_id: str = None) -> Response:
        """Update member role/permissions. Only admin/owner may update. Owner cannot be demoted without transfer."""
        workspace = self._get_workspace(workspace_id)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        membership = get_object_or_404(WorkspaceMember, workspace=workspace, user__id=user_id, is_active=True)
        
        # protect owner
        if getattr(membership, "role", "member") == "owner" and request.user.id != membership.user_id:
            return Response({"detail": "Cannot modify owner."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to use UpdateMemberRoleSerializer first, fall back to WorkspaceMemberCreateSerializer
        try:
            from .serializers import UpdateMemberRoleSerializer
            serializer = UpdateMemberRoleSerializer(
                data=request.data,
                context={'workspace': workspace, 'member': membership, 'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except ImportError:
            # Fallback - directly update the membership
            role = request.data.get('role')
            if role:
                membership.role = role
                membership.save(update_fields=['role'])
            
            permissions = request.data.get('custom_permissions') or request.data.get('permissions')
            if permissions is not None:
                membership.permissions = permissions
                membership.save(update_fields=['permissions'])
        
        return Response(WorkspaceMemberSerializer(membership, context={'request': request}).data)

    def destroy(self, request: Request, workspace_id: str = None, user_id: str = None) -> Response:
        workspace = self._get_workspace(workspace_id)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        membership = get_object_or_404(WorkspaceMember, workspace=workspace, user__id=user_id, is_active=True)
        
        # cannot remove owner
        if getattr(membership, "role", "member") == "owner":
            return Response({"detail": "Cannot remove owner."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Soft delete by setting is_active=False
        membership.is_active = False
        membership.save(update_fields=['is_active'])
        
        # Update workspace counts
        workspace.update_counts()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


# -----------------------------
# WorkspaceInvitationViewSet
# -----------------------------

class WorkspaceInvitationViewSet(viewsets.ViewSet):
    """Manage invitations for a workspace."""

    permission_classes = (IsAuthenticated,)

    def _get_workspace(self, workspace_id: str):
        Workspace = apps.get_model("workspaces", "Workspace")
        return get_object_or_404(Workspace, id=workspace_id)

    def list(self, request: Request, workspace_id: str = None) -> Response:
        workspace = self._get_workspace(workspace_id)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        Invitation = apps.get_model("workspaces", "WorkspaceInvitation")
        # Use status field instead of accepted/revoked
        qs = Invitation.objects.filter(workspace=workspace, status='pending')
        
        serializer = WorkspaceInvitationSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request: Request, workspace_id: str = None) -> Response:
        workspace = self._get_workspace(workspace_id)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = WorkspaceInvitationCreateSerializer(
            data=request.data,
            context={'workspace': workspace, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # The serializer.save() will create the invitation
        invitation = serializer.save()
        
        # Send email (placeholder)
        try:
            if hasattr(invitation, "send_invitation_email"):
                invitation.send_invitation_email()
        except Exception:
            pass
        
        return Response(
            WorkspaceInvitationSerializer(invitation, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request: Request, workspace_id: str = None, pk: str = None) -> Response:
        workspace = self._get_workspace(workspace_id)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        Invitation = apps.get_model("workspaces", "WorkspaceInvitation")
        invitation = get_object_or_404(Invitation, workspace=workspace, id=pk)
        
        # Use status field instead of revoked boolean
        invitation.status = 'revoked'
        invitation.save(update_fields=['status'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="accept")
    @transaction.atomic
    def accept_invitation(self, request: Request, workspace_id: str = None) -> Response:
        """Accept an invitation by token (body: token)."""
        token = request.data.get("token")
        if not token:
            return Response({"detail": "token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        Invitation = apps.get_model("workspaces", "WorkspaceInvitation")
        invitation = Invitation.objects.filter(token=token, status='pending').first()
        
        if not invitation or (invitation.expires_at and invitation.expires_at < timezone.now()):
            return Response({"detail": "Invitation not found or expired."}, status=status.HTTP_404_NOT_FOUND)
        
        # Use the model's accept method
        try:
            invitation.accept(request.user)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail": "Invitation accepted."})

    @action(detail=False, methods=["post"], url_path="decline")
    def decline_invitation(self, request: Request, workspace_id: str = None) -> Response:
        token = request.data.get("token")
        if not token:
            return Response({"detail": "token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        Invitation = apps.get_model("workspaces", "WorkspaceInvitation")
        invitation = Invitation.objects.filter(token=token, status='pending').first()
        
        if not invitation:
            return Response({"detail": "Invitation not found or expired."}, status=status.HTTP_404_NOT_FOUND)
        
        # Use cancel method which sets status to revoked
        invitation.cancel()
        
        return Response({"detail": "Invitation declined."})

    @action(detail=True, methods=["post"], url_path="resend")
    def resend(self, request: Request, workspace_id: str = None, pk: str = None) -> Response:
        workspace = self._get_workspace(workspace_id)
        if not IsWorkspaceAdminOrOwner().has_object_permission(request, self, workspace):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        Invitation = apps.get_model("workspaces", "WorkspaceInvitation")
        invitation = get_object_or_404(Invitation, workspace=workspace, id=pk)
        
        # Regenerate token and expiry
        invitation.token = uuid.uuid4().hex
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.status = 'pending'  # Reset status to pending
        invitation.save(update_fields=['token', 'expires_at', 'status'])
        
        try:
            if hasattr(invitation, "send_invitation_email"):
                invitation.send_invitation_email()
        except Exception:
            pass
        
        return Response({"detail": "Invitation resent."})


# -----------------------------
# WorkspaceStatsView
# -----------------------------

class WorkspaceStatsView(APIView):
    """Return workspace statistics such as member counts, project/task status counts, activity metrics, storage usage."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, workspace_id: str = None) -> Response:
        Workspace = apps.get_model("workspaces", "Workspace")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        # permission
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
            return Response({"detail": "Not a member of this workspace."}, status=status.HTTP_403_FORBIDDEN)
        # member count by role
        member_counts = list(WorkspaceMember.objects.filter(workspace=workspace).values("role").annotate(count=Count("id")))
        # project counts by status
        Project = apps.get_model("projects", "Project") if apps.is_installed("apps.projects") or apps.is_installed("projects") else None
        project_counts = []
        if Project:
            project_counts = list(Project.objects.filter(workspace=workspace).values("status").annotate(count=Count("id")))
        # task counts by status
        Task = apps.get_model("tasks", "Task") if apps.is_installed("apps.tasks") or apps.is_installed("tasks") else None
        task_counts = []
        if Task:
            task_counts = list(Task.objects.filter(project__workspace=workspace).values("status").annotate(count=Count("id")))
        # activity metrics last 30 days
        Activity = apps.get_model("workspaces", "WorkspaceActivity") if apps.is_installed("apps.workspaces") or apps.is_installed("workspaces") else None
        activity_metrics = {}
        if Activity:
            since = timezone.now() - timedelta(days=30)
            recent = Activity.objects.filter(workspace=workspace, timestamp__gte=since)
            activity_metrics = list(recent.values("action").annotate(count=Count("id")))
        # storage usage (if workspace has storage field or related model)
        storage_usage = getattr(workspace, "storage_used_bytes", None) or 0
        result = {
            "members_by_role": member_counts,
            "projects_by_status": project_counts,
            "tasks_by_status": task_counts,
            "activity_metrics_last_30_days": activity_metrics,
            "storage_usage_bytes": storage_usage,
        }
        return Response(result)


# -----------------------------
# WorkspaceActivityView
# -----------------------------

class WorkspaceActivityView(APIView):
    """Return activity feed for a workspace.

    Query params:
    - start, end (ISO dates) to filter by range
    - action (comma separated) filter by action types
    - page / page_size handled manually
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, workspace_id: str = None) -> Response:
        Workspace = apps.get_model("workspaces", "Workspace")
        workspace = get_object_or_404(Workspace, id=workspace_id)
        WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
        if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
            return Response({"detail": "Not a member."}, status=status.HTTP_403_FORBIDDEN)
        Activity = apps.get_model("workspaces", "WorkspaceActivity")
        qs = Activity.objects.filter(workspace=workspace) if Activity else []
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if start:
            try:
                qs = qs.filter(timestamp__gte=start)
            except Exception:
                pass
        if end:
            try:
                qs = qs.filter(timestamp__lte=end)
            except Exception:
                pass
        action_types = request.query_params.get("action")
        if action_types:
            action_list = [a.strip() for a in action_types.split(",") if a.strip()]
            qs = qs.filter(action__in=action_list)
        # ordering recent first
        if hasattr(qs, "order_by"):
            qs = qs.order_by("-timestamp")
        # pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = WorkspaceActivitySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# -----------------------------
# WorkspaceSearchView
# -----------------------------

class WorkspaceSearchView(APIView):
    """Search across workspace content: projects, tasks, messages.

    Query params:
    - q (required) search query
    - workspace_id (optional) restrict to workspace
    - types (comma separated) types to include: projects,tasks,messages
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        q = request.query_params.get("q")
        if not q:
            return Response({"detail": "q parameter required."}, status=status.HTTP_400_BAD_REQUEST)
        workspace_id = request.query_params.get("workspace_id")
        types = request.query_params.get("types")
        types = [t.strip() for t in types.split(",")] if types else ["projects", "tasks", "messages"]

        results: Dict[str, list] = defaultdict(list)
        # restrict to workspace if provided
        if workspace_id:
            Workspace = apps.get_model("workspaces", "Workspace")
            workspace = get_object_or_404(Workspace, id=workspace_id)
            WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
            if not WorkspaceMember.objects.filter(workspace=workspace, user=request.user).exists():
                return Response({"detail": "Not a member."}, status=status.HTTP_403_FORBIDDEN)
        else:
            workspace = None

        if "projects" in types:
            Project = apps.get_model("projects", "Project") if apps.is_installed("apps.projects") or apps.is_installed("projects") else None
            if Project:
                qs = Project.objects.filter(Q(name__icontains=q) | Q(description__icontains=q))
                if workspace:
                    qs = qs.filter(workspace=workspace)
                qs = qs[:50]
                results["projects"] = [{"id": p.id, "name": getattr(p, "name", ""), "excerpt": getattr(p, "description", "")[:200]} for p in qs]

        if "tasks" in types:
            Task = apps.get_model("tasks", "Task") if apps.is_installed("apps.tasks") or apps.is_installed("tasks") else None
            if Task:
                qs = Task.objects.filter(Q(title__icontains=q) | Q(description__icontains=q))
                if workspace:
                    qs = qs.filter(project__workspace=workspace)
                qs = qs[:50]
                results["tasks"] = [{"id": t.id, "title": getattr(t, "title", ""), "excerpt": getattr(t, "description", "")[:200]} for t in qs]

        if "messages" in types:
            Message = apps.get_model("messages", "Message") if apps.is_installed("apps.messages") or apps.is_installed("messages") else None
            if Message:
                qs = Message.objects.filter(Q(body__icontains=q))
                if workspace:
                    qs = qs.filter(channel__workspace=workspace)
                qs = qs[:50]
                results["messages"] = [{"id": m.id, "excerpt": getattr(m, "body", "")[:300], "author_id": getattr(m, "author_id", None)} for m in qs]

        return Response(results)
