from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ─────────────────────────────────────
# 📌 Admin Customization
# ─────────────────────────────────────
admin.site.site_header = "CollabSpace AI Admin"
admin.site.site_title = "CollabSpace AI Admin Portal"
admin.site.index_title = "Welcome to CollabSpace AI Dashboard"

# ─────────────────────────────────────
# 📌 Swagger Schema View
# ─────────────────────────────────────
schema_view = get_schema_view(
    openapi.Info(
        title="CollabSpace AI API",
        default_version="v1",
        description="API documentation for CollabSpace AI backend.",
        contact=openapi.Contact(email="support@collabspace.ai"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# ─────────────────────────────────────
# 📌 Health Check Views
# ─────────────────────────────────────
def health_check(request):
    from django.http import JsonResponse
    return JsonResponse({"status": "ok", "service": "CollabSpace AI Backend"})

def db_health_check(request):
    from django.http import JsonResponse
    from django.db import connections
    try:
        connections["default"].cursor()
        return JsonResponse({"database": "connected"})
    except Exception as e:
        return JsonResponse({"database": "error", "details": str(e)}, status=500)

# ─────────────────────────────────────
# 📌 URL PATTERNS
# ─────────────────────────────────────
urlpatterns = [
    # Admin Panel
    path("admin/", admin.site.urls),

    # Health Checks
    path("health/", health_check, name="health-check"),
    path("health/db/", db_health_check, name="db-health-check"),

    # API v1 Routes (namespaced per app inside apps/)
    path("api/v1/auth/", include(("apps.authentication.urls", "authentication"), namespace="authentication")),
    path("api/v1/core/", include(("apps.core.urls", "core"), namespace="core")),
    path("api/v1/workspaces/", include(("apps.workspaces.urls", "workspaces"), namespace="workspaces")),
    path("api/v1/projects/", include(("apps.projects.urls", "projects"), namespace="projects")),
    path("api/v1/tasks/", include(("apps.tasks.urls", "tasks"), namespace="tasks")),
    path("api/v1/ai/", include(("apps.ai_features.urls", "ai_features"), namespace="ai_features")),
    path("api/v1/messaging/", include(("apps.messaging.urls", "messaging"), namespace="messaging")),
    path("api/v1/files/", include(("apps.files.urls", "files"), namespace="files")),
    path("api/v1/notifications/", include(("apps.notifications.urls", "notifications"), namespace="notifications")),
    path("api/v1/analytics/", include(("apps.analytics.urls", "analytics"), namespace="analytics")),
    path("api/v1/integrations/", include(("apps.integrations.urls", "integrations"), namespace="integrations")),

    # API Documentation
    path("api/docs/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-docs"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc-docs"),
]

# ─────────────────────────────────────
# 📌 Static + Media in Development
# ─────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ─────────────────────────────────────
# 📌 Custom Error Handlers
# ─────────────────────────────────────
def custom_page_not_found(request, exception):
    from django.http import JsonResponse
    return JsonResponse({"error": "The requested resource was not found."}, status=404)

def custom_server_error(request):
    from django.http import JsonResponse
    return JsonResponse({"error": "Internal server error."}, status=500)

handler404 = "collabspace_backend.urls.custom_page_not_found"
handler500 = "collabspace_backend.urls.custom_server_error"
