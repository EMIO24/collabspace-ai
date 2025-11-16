from typing import Any, Dict, Optional
from uuid import uuid4

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.template.defaultfilters import slugify
from django.urls import reverse
from rest_framework import serializers

User = get_user_model()

# Lazy model retrieval to avoid circular imports
Workspace = apps.get_model("workspaces", "Workspace")
WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
WorkspaceInvitation = apps.get_model("workspaces", "WorkspaceInvitation")


def _get_allowed_roles() -> list:
    """Return a list of valid role keys from WorkspaceMember if available,
    otherwise fall back to sensible defaults.
    """
    if hasattr(WorkspaceMember, "ROLE_CHOICES"):
        return [r[0] for r in WorkspaceMember.ROLE_CHOICES]
    # sensible fallback
    return ["owner", "admin", "member", "viewer"]


def _generate_unique_slug(name: str) -> str:
    base = slugify(name)[:80] or "workspace"
    # try to create a reasonably unique slug; append uuid4 short if collision
    candidate = base
    if Workspace.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{uuid4().hex[:8]}"
        # still unlikely to collide, but ensure uniqueness
        while Workspace.objects.filter(slug=candidate).exists():
            candidate = f"{base}-{uuid4().hex[:8]}"
    return candidate


class MinimalUserSerializer(serializers.ModelSerializer):
    """Nested, small user representation used in multiple places."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "full_name", "avatar")
        read_only_fields = fields

    def get_full_name(self, obj):
        # support both get_full_name and first_name/last_name
        if hasattr(obj, "get_full_name"):
            return obj.get_full_name()
        return f"{getattr(obj, 'first_name', '')} {getattr(obj, 'last_name', '')}".strip()


class WorkspaceListSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    plan_type = serializers.CharField(source="plan", read_only=True)

    class Meta:
        model = Workspace
        fields = (
            "id",
            "name",
            "slug",
            "logo",
            "is_public",
            "plan_type",
            "member_count",
            "project_count",
            "role",
        )

    def get_member_count(self, obj: Workspace) -> int:
        try:
            return obj.members.count()
        except Exception:
            return 0

    def get_project_count(self, obj: Workspace) -> int:
        try:
            return obj.projects.count()
        except Exception:
            return 0

    def get_role(self, obj: Workspace) -> Optional[str]:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        try:
            membership = WorkspaceMember.objects.filter(workspace=obj, user=request.user).first()
            return membership.role if membership else None
        except Exception:
            return None


class OwnerNestedSerializer(MinimalUserSerializer):
    class Meta(MinimalUserSerializer.Meta):
        fields = ("id", "username", "email", "full_name", "avatar")


class WorkspaceStatsSerializer(serializers.Serializer):
    member_count = serializers.IntegerField(read_only=True)
    project_count = serializers.IntegerField(read_only=True)
    task_count = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    pending_tasks = serializers.IntegerField(read_only=True)
    recent_activity_count = serializers.IntegerField(read_only=True)
    storage_used = serializers.IntegerField(read_only=True)


class WorkspaceDetailSerializer(serializers.ModelSerializer):
    owner = OwnerNestedSerializer(read_only=True)
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        # include all model fields if possible; fall back to common fields
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "logo",
            "is_public",
            "owner",
            "created_at",
            "updated_at",
            "settings",
            "plan",
            "role",
            "permissions",
            "stats",
        )

    def get_role(self, obj: Workspace) -> Optional[str]:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = WorkspaceMember.objects.filter(workspace=obj, user=request.user).first()
        return membership.role if membership else None

    def get_permissions(self, obj: Workspace) -> Dict[str, Any]:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return {}
        membership = WorkspaceMember.objects.filter(workspace=obj, user=request.user).first()
        if not membership:
            return {}
        # membership.permissions might be a dict/JSONField or a related set
        perms = getattr(membership, "permissions", None)
        if perms is None:
            # try to build permissive defaults based on role
            role = getattr(membership, "role", "member")
            if role == "owner":
                return {"manage_workspace": True, "manage_members": True, "manage_projects": True}
            if role == "admin":
                return {"manage_workspace": False, "manage_members": True, "manage_projects": True}
            return {"manage_workspace": False, "manage_members": False, "manage_projects": False}
        return perms

    def get_stats(self, obj: Workspace) -> Dict[str, Any]:
        # compute the stats in a defensive way
        try:
            member_count = obj.members.count()
        except Exception:
            member_count = 0
        try:
            project_count = obj.projects.count()
        except Exception:
            project_count = 0
        try:
            task_qs = getattr(obj, "tasks", None)
            task_count = task_qs.count() if task_qs is not None else 0
            completed_tasks = task_qs.filter(status="completed").count() if task_qs is not None else 0
            pending_tasks = task_count - completed_tasks
        except Exception:
            task_count = completed_tasks = pending_tasks = 0
        # recent activity & storage may be available via methods or fields
        recent_activity_count = getattr(obj, "recent_activity_count", 0) or 0
        storage_used = getattr(obj, "storage_used", 0) or 0
        return {
            "member_count": member_count,
            "project_count": project_count,
            "task_count": task_count,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "recent_activity_count": recent_activity_count,
            "storage_used": storage_used,
        }


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    owner = MinimalUserSerializer(read_only=True)

    class Meta:
        model = Workspace
        fields = ("id", "name", "slug", "description", "logo", "is_public", "owner", "settings")
        read_only_fields = ("id", "slug", "owner")

    def validate_name(self, value: str) -> str:
        """Ensure the user doesn't already have a workspace with this name."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return value
        owner = request.user
        if Workspace.objects.filter(owner=owner, name__iexact=value).exists():
            raise serializers.ValidationError("You already have a workspace with this name.")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Workspace:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to create a workspace.")
        owner = request.user
        # generate slug
        name = validated_data.get("name")
        slug = _generate_unique_slug(name)
        validated_data["slug"] = slug
        # set owner
        validated_data["owner"] = owner
        # create default settings if missing
        settings = validated_data.get("settings")
        if settings is None:
            validated_data["settings"] = {
                "notifications": True,
                "default_visibility": "private",
            }
        try:
            with transaction.atomic():
                ws = super().create(validated_data)
                # create the owner membership
                try:
                    WorkspaceMember.objects.create(workspace=ws, user=owner, role="owner")
                except Exception:
                    # if membership creation fails, roll back
                    raise
                # hook for additional default resources - do not assume presence of models
                if hasattr(ws, "create_default_resources"):
                    try:
                        ws.create_default_resources()
                    except Exception:
                        # don't hide a workspace creation error if defaults fail; but warn in logs
                        pass
                return ws
        except IntegrityError:
            raise serializers.ValidationError("A workspace with that slug or name already exists.")


class WorkspaceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ("name", "description", "logo", "settings")

    def validate_name(self, value: str) -> str:
        # ensure name doesn't conflict with another workspace owned by same owner
        instance: Workspace = getattr(self, "instance", None)
        request = self.context.get("request")
        owner = instance.owner if instance else getattr(request, "user", None)
        if not owner:
            return value
        qs = Workspace.objects.filter(owner=owner, name__iexact=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Another workspace with this name already exists for your account.")
        return value

    def update(self, instance: Workspace, validated_data: Dict[str, Any]) -> Workspace:
        name = validated_data.get("name")
        if name and name != instance.name:
            instance.slug = _generate_unique_slug(name)
        return super().update(instance, validated_data)


class WorkspaceMemberUserSerializer(MinimalUserSerializer):
    pass


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = WorkspaceMemberUserSerializer(read_only=True)
    invited_by = WorkspaceMemberUserSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ("user", "role", "permissions", "joined_at", "invited_by")
        read_only_fields = ("joined_at",)


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    user_id = serializers.UUIDField(required=False)
    role = serializers.ChoiceField(choices=[(r, r) for r in _get_allowed_roles()])
    custom_permissions = serializers.JSONField(required=False, allow_null=True)

    def validate(self, attrs):
        email = attrs.get("email")
        user_id = attrs.get("user_id")
        if not email and not user_id:
            raise serializers.ValidationError("Either 'email' or 'user_id' is required to add a member.")
        request = self.context.get("request")
        workspace: Workspace = self.context.get("workspace")
        if not workspace:
            raise serializers.ValidationError("Workspace context is required.")
        # resolve user if email provided
        user = None
        if email:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                # This is allowed — invitation flow will create an invitation instead of direct add
                attrs["resolved_user"] = None
            else:
                attrs["resolved_user"] = user
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found for the provided user_id.")
            attrs["resolved_user"] = user
        # check membership
        if attrs.get("resolved_user"):
            if WorkspaceMember.objects.filter(workspace=workspace, user=attrs["resolved_user"]).exists():
                raise serializers.ValidationError("The specified user is already a member of this workspace.")
        return attrs

    def save(self, **kwargs):
        workspace: Workspace = self.context["workspace"]
        resolved_user = self.validated_data.get("resolved_user")
        role = self.validated_data.get("role")
        custom_permissions = self.validated_data.get("custom_permissions")
        # if resolved_user is None, create an invitation
        if resolved_user is None:
            # create invitation record
            invitation = WorkspaceInvitation.objects.create(
                workspace=workspace,
                email=self.validated_data.get("email"),
                role=role,
                invited_by=self.context["request"].user,
                custom_permissions=custom_permissions,
            )
            return invitation
        # otherwise create membership
        member = WorkspaceMember.objects.create(
            workspace=workspace,
            user=resolved_user,
            role=role,
            permissions=custom_permissions or {},
        )
        return member


class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[(r, r) for r in _get_allowed_roles()])
    custom_permissions = serializers.JSONField(required=False, allow_null=True)

    def validate(self, attrs):
        workspace: Workspace = self.context.get("workspace")
        member: WorkspaceMember = self.context.get("member")
        request = self.context.get("request")
        if not workspace or not member:
            raise serializers.ValidationError("Workspace and member context are required.")
        # cannot change owner role
        if getattr(member, "role", None) == "owner":
            raise serializers.ValidationError("Cannot change the role of the workspace owner.")
        # validate demotion of self (if owner) - prevent owner demoting themself
        if request and getattr(request.user, "pk", None) == getattr(member.user, "pk", None):
            # allow self-role-change only if not owner
            if getattr(member, "role", None) == "owner":
                raise serializers.ValidationError("Workspace owner cannot demote themselves.")
        return attrs

    def save(self, **kwargs):
        member: WorkspaceMember = self.context["member"]
        member.role = self.validated_data["role"]
        if "custom_permissions" in self.validated_data:
            member.permissions = self.validated_data.get("custom_permissions") or {}
        member.save()
        return member


class WorkspaceInvitationSerializer(serializers.ModelSerializer):
    invitation_url = serializers.SerializerMethodField()
    invited_by = MinimalUserSerializer(read_only=True)

    class Meta:
        model = WorkspaceInvitation
        fields = (
            "id",
            "email",
            "workspace",
            "role",
            "token",
            "status",
            "created_at",
            "expires_at",
            "invited_by",
            "invitation_url",
        )
        read_only_fields = ("token", "status", "created_at")

    def get_invitation_url(self, obj: WorkspaceInvitation) -> Optional[str]:
        request = self.context.get("request")
        try:
            if request:
                view_name = "workspaces:accept-invitation"
                return request.build_absolute_uri(reverse(view_name, kwargs={"token": obj.token}))
        except Exception:
            return None
        return None


class SendInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[(r, r) for r in _get_allowed_roles()])
    message = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        # check already a member
        workspace: Workspace = self.context.get("workspace")
        if not workspace:
            raise serializers.ValidationError("Workspace context is required.")
        if User.objects.filter(email__iexact=value).exists():
            user = User.objects.get(email__iexact=value)
            if WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
                raise serializers.ValidationError("This email belongs to a user who is already a member of the workspace.")
        # check already invited
        if WorkspaceInvitation.objects.filter(workspace=workspace, email__iexact=value, status__in=("pending",)).exists():
            raise serializers.ValidationError("An invitation has already been sent to this email for this workspace.")
        return value

    def save(self, **kwargs):
        workspace: Workspace = self.context["workspace"]
        inviter = self.context["request"].user
        invite = WorkspaceInvitation.objects.create(
            workspace=workspace,
            email=self.validated_data["email"],
            role=self.validated_data["role"],
            message=self.validated_data.get("message", ""),
            invited_by=inviter,
        )
        return invite


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value: str) -> str:
        try:
            invitation = WorkspaceInvitation.objects.get(token=value)
        except WorkspaceInvitation.DoesNotExist:
            raise serializers.ValidationError("Invitation token not found or invalid.")
        if invitation.is_expired():
            raise serializers.ValidationError("Invitation token has expired.")
        if invitation.status != "pending":
            raise serializers.ValidationError("This invitation is not pending and cannot be accepted.")
        # stash invitation for save
        self._invitation = invitation
        return value

    def save(self, **kwargs):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required to accept an invitation.")
        user = request.user
        invitation: WorkspaceInvitation = getattr(self, "_invitation", None)
        if not invitation:
            raise serializers.ValidationError("Invitation not validated.")
        # create membership
        if WorkspaceMember.objects.filter(workspace=invitation.workspace, user=user).exists():
            # already a member
            invitation.status = "accepted"
            invitation.save()
            return WorkspaceMember.objects.get(workspace=invitation.workspace, user=user)
        member = WorkspaceMember.objects.create(
            workspace=invitation.workspace,
            user=user,
            role=invitation.role,
            permissions=getattr(invitation, "custom_permissions", {}) or {},
        )
        invitation.status = "accepted"
        invitation.accepted_by = user
        invitation.save()
        return member


# Stats serializer (concrete implementation)
class WorkspaceStatsReadSerializer(serializers.Serializer):
    member_count = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    pending_tasks = serializers.SerializerMethodField()
    recent_activity_count = serializers.SerializerMethodField()
    storage_used = serializers.SerializerMethodField()

    def get_member_count(self, obj: Workspace) -> int:
        try:
            return obj.members.count()
        except Exception:
            return 0

    def get_project_count(self, obj: Workspace) -> int:
        try:
            return obj.projects.count()
        except Exception:
            return 0

    def get_task_count(self, obj: Workspace) -> int:
        try:
            qs = getattr(obj, "tasks", None)
            return qs.count() if qs is not None else 0
        except Exception:
            return 0

    def get_completed_tasks(self, obj: Workspace) -> int:
        try:
            qs = getattr(obj, "tasks", None)
            return qs.filter(status="completed").count() if qs is not None else 0
        except Exception:
            return 0

    def get_pending_tasks(self, obj: Workspace) -> int:
        try:
            return self.get_task_count(obj) - self.get_completed_tasks(obj)
        except Exception:
            return 0

    def get_recent_activity_count(self, obj: Workspace) -> int:
        return getattr(obj, "recent_activity_count", 0) or 0

    def get_storage_used(self, obj: Workspace) -> int:
        return getattr(obj, "storage_used", 0) or 0
