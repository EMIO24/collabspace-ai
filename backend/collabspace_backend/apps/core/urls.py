from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("health/", views.HealthCheckView.as_view(), name="health"),
    path("status/", views.SystemStatusView.as_view(), name="status"),
    path("version/", views.APIVersionView.as_view(), name="version"),
]
