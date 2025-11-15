import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from django.utils.deprecation import MiddlewareMixin  # still useful fallback
from django.utils.timezone import now as tz_now
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


class ActivityTrackingMiddleware:
    """
    Middleware to update user's last_activity timestamp.
    Should be placed after AuthenticationMiddleware so request.user is available.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        try:
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                # update last_activity only on API or authenticated requests
                if hasattr(user, "last_activity"):
                    # Use update query to avoid full save hooks if available
                    try:
                        user.__class__.objects.filter(pk=user.pk).update(last_activity=tz_now())
                    except Exception:
                        # fallback to attribute set + save
                        user.last_activity = tz_now()
                        user.save(update_fields=["last_activity"])
        except Exception:
            logger.exception("Failed to update last_activity for user")
        return response


class RequestLoggingMiddleware:
    """
    Log pertinent request info, status and timings. Keep logs concise to avoid sensitive data.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.time()
        try:
            response = self.get_response(request)
            elapsed = time.time() - start
            logger.info(
                "%s %s %s %s %.3fs",
                request.method,
                request.get_full_path(),
                getattr(request, "user", None) and getattr(request.user, "id", None),
                getattr(response, "status_code", "NA"),
                elapsed,
            )
            return response
        except Exception as exc:
            elapsed = time.time() - start
            logger.exception("Request error: %s %s %.3fs", request.method, request.get_full_path(), elapsed)
            raise


class APIVersionMiddleware:
    """
    Extract API version from Accept headers or URL and attach to request.api_version.
    Priority:
      1. view kwargs (if URLConf includes version)
      2. X-API-Version header
      3. Accept header like 'application/vnd.collabspace.v1+json'
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        version = None
        # 1. header
        version = request.headers.get("X-API-Version")
        # 2. Accept header parsing
        if not version:
            accept = request.headers.get("Accept", "")
            # naive parse
            if "vnd." in accept and "+" in accept:
                # e.g. application/vnd.collabspace.v1+json
                try:
                    parts = accept.split("vnd.")[1]
                    version_part = parts.split("+")[0]
                    # version_part might be collabspace.v1
                    if "." in version_part:
                        version = version_part.split(".")[-1]
                except Exception:
                    version = None
        # 3. fallback from urlconf (some views may set view.kwargs['version'])
        request.api_version = version
        return self.get_response(request)


class RateLimitMiddleware:
    """
    Lightweight per-IP or per-user rate limiting using in-memory store.
    For production, use redis or a proper rate limiter. This is a conservative fallback.
    Configuration:
      settings.RATE_LIMIT = {
          'DEFAULT': (1000, 60*60),  # 1000 requests per hour
          'ANONYMOUS': (100, 60),    # 100 requests per minute
      }
    Note: This implementation is intentionally simple; prefer a robust solution (throttling in DRF or redis).
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        # in-memory store: {key: (count, reset_ts)}
        self._store = {}

    def _get_limits(self):
        return getattr(settings, "RATE_LIMIT", {"DEFAULT": (1000, 3600), "ANONYMOUS": (100, 60)})

    def _get_key(self, request: HttpRequest) -> str:
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return f"user:{user.pk}"
        else:
            # fallback to IP
            ip = request.META.get("REMOTE_ADDR") or request.META.get("HTTP_X_FORWARDED_FOR", "anon")
            return f"ip:{ip}"

    def __call__(self, request: HttpRequest):
        limits = self._get_limits()
        anon_limit, anon_window = limits.get("ANONYMOUS", (100, 60))
        default_limit, default_window = limits.get("DEFAULT", (1000, 3600))
        key = self._get_key(request)
        limit, window = (default_limit, default_window) if key.startswith("user:") else (anon_limit, anon_window)

        now_ts = int(time.time())
        entry = self._store.get(key)
        if entry:
            count, reset_ts = entry
            if now_ts > reset_ts:
                count = 0
                reset_ts = now_ts + window
        else:
            count = 0
            reset_ts = now_ts + window

        if count >= limit:
            # Rate limited
            retry_after = reset_ts - now_ts
            logger.warning("Rate limit exceeded for %s", key)
            return JsonResponse({"detail": "Rate limit exceeded."}, status=429, headers={"Retry-After": str(retry_after)})
        # increment and store
        self._store[key] = (count + 1, reset_ts)
        return self.get_response(request)


class CORSMiddleware:
    """
    Minimal CORS header helper. If you are using django-cors-headers, you can skip this middleware.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.allow_all = getattr(settings, "CORS_ALLOW_ALL", False)
        self.allowed_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        origin = request.headers.get("Origin")
        if self.allow_all:
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-API-Version"
        elif origin and origin in self.allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
            response.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
            response.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, X-API-Version")
        return response
