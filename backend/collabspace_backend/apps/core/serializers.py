from datetime import datetime
from typing import Any, Dict, Optional

from rest_framework import serializers


class TimestampSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", required=False, allow_null=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", required=False, allow_null=True)

    # Helper to produce timestamps from model instances
    @staticmethod
    def from_instance(instance) -> Dict[str, Optional[str]]:
        created = getattr(instance, "created_at", None) or getattr(instance, "created", None)
        updated = getattr(instance, "updated_at", None) or getattr(instance, "modified", None)
        return {
            "created_at": created,
            "updated_at": updated,
        }


class ErrorSerializer(serializers.Serializer):
    status = serializers.CharField(default="error")
    message = serializers.CharField()
    errors = serializers.DictField(child=serializers.CharField(), required=False, allow_null=True)


class SuccessSerializer(serializers.Serializer):
    status = serializers.CharField(default="success")
    message = serializers.CharField()
    data = serializers.DictField(child=serializers.JSONField(), required=False, allow_null=True)


class PaginationSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
