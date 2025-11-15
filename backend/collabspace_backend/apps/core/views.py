from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import platform
import psutil
import django

class HealthCheckView(APIView):
    """
    Simple health check endpoint
    """
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class SystemStatusView(APIView):
    """
    Returns detailed system status: CPU, memory, etc.
    """
    def get(self, request):
        memory = psutil.virtual_memory()
        return Response({
            "cpu_count": psutil.cpu_count(),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_total": memory.total,
            "memory_available": memory.available,
            "memory_percent": memory.percent,
            "platform": platform.system(),
            "platform_release": platform.release(),
        }, status=status.HTTP_200_OK)


class APIVersionView(APIView):
    """
    Returns Django and API version information
    """
    def get(self, request):
        return Response({
            "django_version": django.get_version(),
            "api_version": "1.0.0"
        }, status=status.HTTP_200_OK)
