import csv
import io
import logging
from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html
from django.apps import apps
from django import forms

logger = logging.getLogger(__name__)

Workspace = apps.get_model("workspaces", "Workspace")
WorkspaceMember = apps.get_model("workspaces", "WorkspaceMember")
WorkspaceInvitation = apps.get_model("workspaces", "WorkspaceInvitation")


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    # Added "slug" to list_display as it is a key identifier used in search and export.
    list_display = ("id", "name", "slug", "owner", "plan_type", "is_public", "member_count", "created_at")
    search_fields = ("name", "slug", "owner__username", "owner__email")
    list_filter = ("plan_type", "is_public", "created_at")
    readonly_fields = ("member_count",)
    actions = ["export_workspace_data", "transfer_ownership_action"]

    def export_workspace_data(self, request, queryset):
        """
        Export selected workspace(s) to CSV. This includes basic workspace fields
        and member_count. For production you might export nested data as separate files.
        """
        if queryset.count() == 0:
            self.message_user(request, "No workspaces selected.", level=messages.WARNING)
            return

        # Build CSV in-memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "slug", "owner_id", "owner_username", "plan_type", "is_public", "member_count", "created_at", "description"])

        for ws in queryset:
            writer.writerow([
                ws.pk,
                ws.name,
                ws.slug,
                getattr(ws.owner, "pk", ""),
                getattr(ws.owner, "username", ""),
                ws.plan_type,
                ws.is_public,
                ws.member_count,
                ws.created_at.isoformat() if getattr(ws, "created_at", None) else "",
                (ws.description or "").replace("\n", " "),
            ])

        output.seek(0)
        response = HttpResponse(output, content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=workspaces_export.csv"
        return response

    export_workspace_data.short_description = "Export selected workspace(s) data as CSV"

    def transfer_ownership_action(self, request, queryset):
        """
        Transfer ownership admin action:
        - If multiple workspaces are selected, transfers ownership for each to the 'first admin member' found.
        - If no admin member exists, the action fails for that workspace.
        Note: for robust transfer (e.g. specifying new owner) implement an admin form.
        """
        success, failed = 0, []
        for ws in queryset:
            try:
                # Find an admin member that is not the current owner
                admin_member = WorkspaceMember.objects.filter(workspace=ws, role__in=["admin", "maintainer"]).exclude(user=ws.owner).first()
                if not admin_member:
                    failed.append(ws.name)
                    continue
                ws.owner = admin_member.user
                ws.save(update_fields=["owner"])
                success += 1
            except Exception as e:
                logger.exception("Failed transfer ownership for %s", ws)
                failed.append(ws.name)
        msg = f"Ownership transferred for {success} workspace(s)."
        if failed:
            msg += f" Failed for: {', '.join(failed)}"
        self.message_user(request, msg, level=messages.INFO)

    transfer_ownership_action.short_description = "Transfer ownership to first admin member (best-effort)"

    def get_urls(self):
        urls = super().get_urls()
        # Add a custom admin URL if necessary in future
        return urls


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "workspace", "user", "role", "joined_at", "is_active")
    search_fields = ("user__username", "user__email", "workspace__name")
    # Added "workspace" to list_filter to allow filtering members by the workspace they belong to.
    list_filter = ("workspace", "role", "is_active", "joined_at")


@admin.register(WorkspaceInvitation)
class WorkspaceInvitationAdmin(admin.ModelAdmin):
    list_display = ("id", "workspace", "email", "invited_by", "status", "created_at")
    search_fields = ("email", "workspace__name", "invited_by__username")
    list_filter = ("status", "workspace", "created_at")
    actions = ["bulk_approve_invitations", "export_invitations"]

    def bulk_approve_invitations(self, request, queryset):
        """
        Approve pending invitations in bulk. Approved invitations will be marked and
        possibly converted to membership depending on your app logic.
        """
        count = 0
        for inv in queryset.filter(status="pending"):
            try:
                inv.status = "approved"
                inv.save(update_fields=["status"])
                count += 1
            except Exception:
                logger.exception("Failed to approve invitation %s", inv.pk)
        self.message_user(request, f"{count} invitation(s) approved.", level=messages.SUCCESS)

    bulk_approve_invitations.short_description = "Bulk approve selected pending invitations"

    def export_invitations(self, request, queryset):
        """
        Export invitation list to CSV
        """
        if not queryset.exists():
            self.message_user(request, "No invitations selected.", level=messages.WARNING)
            return
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "workspace", "email", "invited_by", "status", "created_at"])
        for inv in queryset:
            writer.writerow([
                inv.pk,
                getattr(inv.workspace, "name", ""),
                inv.email,
                getattr(inv.invited_by, "username", "") if getattr(inv, "invited_by", None) else "",
                inv.status,
                inv.created_at.isoformat() if getattr(inv, "created_at", None) else "",
            ])
        output.seek(0)
        response = HttpResponse(output, content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=workspace_invitations.csv"
        return response

    export_invitations.short_description = "Export selected invitations to CSV"