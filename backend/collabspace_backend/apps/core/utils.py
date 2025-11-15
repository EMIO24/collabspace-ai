import logging
import math
import os
import random
import re
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.text import slugify

logger = logging.getLogger(__name__)


def format_api_response(data: Any = None, message: str = "OK", status: str = "success") -> Dict[str, Any]:
    """
    Standardized API response format.
    """
    return {"status": status, "message": message, "data": data}


def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate a URL-safe slug from text. Ensures uniqueness should be handled by caller if needed.
    """
    s = slugify(text)[:max_length]
    if not s:
        # fallback to random slug
        s = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return s


def get_client_ip(request) -> Optional[str]:
    """
    Safely obtain client IP (checking X-Forwarded-For).
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        ip = xff.split(",")[0].strip()
        return ip
    return request.META.get("REMOTE_ADDR")


def send_email_template(
    user,
    template: str,
    context: Dict[str, Any],
    subject: Optional[str] = None,
    from_email: Optional[str] = None,
    to_email: Optional[str] = None,
):
    """
    Render a template and send an email. Template should have at least 'subject' and 'body' blocks or partials.
    Example template: 'emails/welcome.html' and 'emails/welcome.txt'
    """
    try:
        txt = render_to_string(f"{template}.txt", {**context, "user": user})
        html = render_to_string(f"{template}.html", {**context, "user": user})
        subject = subject or context.get("subject") or f"Message from {getattr(settings, 'SITE_NAME', 'CollabSpace')}"
        from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
        to_email = to_email or getattr(user, "email", None)
        if not to_email:
            logger.warning("No recipient email available for send_email_template")
            return False
        msg = EmailMultiAlternatives(subject, txt, from_email, [to_email])
        if html:
            msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Failed to send email template %s", template)
        return False


def calculate_time_difference(start: datetime, end: datetime) -> Dict[str, int]:
    """
    Return difference between two datetimes in days/hours/minutes/seconds.
    Both datetimes should be timezone-aware or naive consistently.
    """
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        raise ValueError("start and end must be datetime instances")
    delta = end - start if end >= start else start - end
    seconds = int(delta.total_seconds())
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return {"days": days, "hours": hours, "minutes": minutes, "seconds": secs}


def truncate_string(text: str, length: int = 100, ellipsis: str = "...") -> str:
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[: max(0, length - len(ellipsis))] + ellipsis


def generate_random_string(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def validate_file_extension(filename: str, allowed_extensions: Optional[list] = None) -> bool:
    if not allowed_extensions:
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx"]
    ext = os.path.splitext(filename)[1].lower()
    return ext in [e.lower() for e in allowed_extensions]


def get_file_size(file_obj) -> int:
    """
    Returns file size in bytes. Accepts Django UploadedFile or file-like object.
    """
    try:
        # UploadedFile
        return getattr(file_obj, "size", os.fstat(file_obj.fileno()).st_size)
    except Exception:
        try:
            file_obj.seek(0, os.SEEK_END)
            size = file_obj.tell()
            file_obj.seek(0)
            return size
        except Exception:
            logger.exception("Unable to determine file size")
            return 0


def format_bytes(num_bytes: int, precision: int = 2) -> str:
    """
    Human-readable file size.
    """
    if num_bytes is None:
        return "0 B"
    num_bytes = int(num_bytes)
    if num_bytes == 0:
        return "0 B"
    unit_names = ("B", "KB", "MB", "GB", "TB", "PB")
    i = int(math.floor(math.log(max(num_bytes, 1), 1024)))
    p = math.pow(1024, i)
    s = round(num_bytes / p, precision)
    return f"{s} {unit_names[i]}"
