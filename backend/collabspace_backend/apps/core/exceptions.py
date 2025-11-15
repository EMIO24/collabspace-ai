import logging
from typing import Any, Dict
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError, PermissionDenied as DRFPermissionDenied

logger = logging.getLogger(__name__)


# Custom exception types (extend APIException for DRF compatibility)


class WorkspaceNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Workspace not found."
    default_code = "workspace_not_found"


class ProjectNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Project not found."
    default_code = "project_not_found"


class TaskNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Task not found."
    default_code = "task_not_found"


class PermissionDeniedError(DRFPermissionDenied):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class ValidationError(DRFValidationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid input."
    default_code = "invalid"


class AIQuotaExceededError(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "AI quota exceeded for the workspace or account."
    default_code = "ai_quota_exceeded"


class FileUploadError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "File upload failed or invalid file."
    default_code = "file_upload_error"


class WebSocketError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "WebSocket error."
    default_code = "websocket_error"


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that returns consistent JSON structure:
    {
        "status": "error"|"fail",
        "message": "...",
        "errors": {...}  # optional detailed errors
    }
    """
    # Call REST framework's default handler first to get the standard error response.
    response = exception_handler(exc, context)

    # If DRF already produced a response, normalize it
    if response is not None:
        data = {"status": "error", "message": None, "errors": None}
        if isinstance(response.data, dict):
            # get first non-field message if exists
            message = response.data.get("detail") or response.data.get("message")
            errors = {k: v for k, v in response.data.items() if k not in ("detail", "message")}
            data["message"] = message or str(exc)
            data["errors"] = errors if errors else None
        else:
            data["message"] = str(response.data)
        response.data = data
        return response

    # If no response from DRF handler, handle server errors
    logger.exception("Unhandled exception: %s", exc)
    return Response(
        {"status": "error", "message": "Internal server error", "errors": {"detail": str(exc)}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
