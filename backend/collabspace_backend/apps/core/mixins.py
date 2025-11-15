from typing import Any, Dict, Optional

from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status


class SoftDeleteMixin:
    """
    Mixin for viewsets to implement soft-delete behaviour.
    Expects model has 'is_deleted' (BooleanField) and optionally 'deleted_at' datetime.
    Override perform_destroy if model uses different fields.
    """

    def perform_destroy(self, instance):
        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            if hasattr(instance, "deleted_at"):
                from django.utils.timezone import now

                instance.deleted_at = now()
            instance.save(update_fields=[f for f in ("is_deleted", "deleted_at") if hasattr(instance, f)])
        else:
            # fallback to hard delete
            instance.delete()

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimestampMixin:
    """
    Adds timestamps or ensures timestamp fields are returned when serializing.
    Use in list/retrieve views to annotate response with timestamp metadata if needed.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        # If response is a dict-like and object has created/updated, add them
        try:
            if hasattr(response, "data") and isinstance(response.data, dict) and getattr(self, "get_object", None):
                obj = None
                # when retrieving single object
                if hasattr(self, "action") and self.action in ("retrieve",):
                    try:
                        obj = self.get_object()
                    except Exception:
                        obj = None
                if obj:
                    created = getattr(obj, "created_at", None) or getattr(obj, "created", None)
                    updated = getattr(obj, "updated_at", None) or getattr(obj, "modified", None)
                    if created and "created_at" not in response.data:
                        response.data["created_at"] = created
                    if updated and "updated_at" not in response.data:
                        response.data["updated_at"] = updated
        except Exception:
            pass
        return super().finalize_response(request, response, *args, **kwargs)


class OwnershipMixin:
    """
    Filters queryset by owner based on request.user
    Expects model has 'owner' or 'created_by' foreign key to User.
    """

    owner_field = "owner"

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return qs.none()
        # try both owner and created_by
        filter_kwargs = {self.owner_field: user}
        try:
            return qs.filter(**filter_kwargs)
        except Exception:
            # fallback: try created_by
            try:
                return qs.filter(created_by=user)
            except Exception:
                return qs.none()


class WorkspaceFilterMixin:
    """
    Filters by workspace passed in query params or URL kwargs.
    Expects the queryset/model has a 'workspace' FK.
    """

    workspace_kwarg = "workspace_id"
    workspace_query_param = "workspace"

    def get_workspace_id(self):
        return self.kwargs.get(self.workspace_kwarg) or self.request.query_params.get(self.workspace_query_param)

    def filter_by_workspace(self, queryset):
        workspace_id = self.get_workspace_id()
        if not workspace_id:
            return queryset
        try:
            return queryset.filter(workspace_id=workspace_id)
        except Exception:
            return queryset

    def get_queryset(self):
        qs = super().get_queryset()
        return self.filter_by_workspace(qs)
