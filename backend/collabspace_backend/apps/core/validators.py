import imghdr
import io
import json
import logging
import re
from typing import Any, Dict, List

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

try:
    from PIL import Image
except Exception:
    Image = None

logger = logging.getLogger(__name__)


def validate_file_type(file_obj, allowed_types: List[str]):
    """
    Validate a file's content type by extension and simple magic detection.
    allowed_types: list of mime types or file extensions ('.jpg', 'image/png', etc.)
    """
    name = getattr(file_obj, "name", "")
    ext = name.split(".")[-1].lower() if "." in name else ""
    # extension check
    for a in allowed_types:
        if a.startswith(".") and ext == a.lstrip(".").lower():
            return True
        if "/" in a:
            # Mime type check - best effort
            content_type = getattr(file_obj, "content_type", "")
            if content_type and content_type.split(";")[0] == a:
                return True
    # fallback: simple magic
    try:
        header = file_obj.read(512)
        file_obj.seek(0)
        kind = imghdr.what(None, h=header)
        if kind and any(a.lstrip(".").lower() == kind for a in allowed_types if a.startswith(".")):
            return True
    except Exception:
        logger.exception("Error inspecting file header")
    raise ValidationError(_("Invalid file type."))


def validate_file_size(file_obj, max_size_mb: int = 10):
    """
    Validate file size is <= max_size_mb.
    """
    size = getattr(file_obj, "size", None)
    if size is None:
        try:
            file_obj.seek(0, 2)
            size = file_obj.tell()
            file_obj.seek(0)
        except Exception:
            logger.exception("Could not determine file size for validation")
            raise ValidationError(_("Unable to determine file size."))
    max_bytes = max_size_mb * 1024 * 1024
    if size > max_bytes:
        raise ValidationError(_(f"Maximum file size is {max_size_mb} MB."))
    return True


def validate_image_dimensions(file_obj, max_width: int = 2000, max_height: int = 2000):
    """
    Validate that image dimensions are within provided limits. Requires Pillow.
    Accepts Django InMemoryUploadedFile or file-like object.
    """
    if Image is None:
        logger.error("Pillow is not installed; cannot validate image dimensions")
        return True  # fallback: cannot validate
    try:
        img = Image.open(file_obj)
        width, height = img.size
        file_obj.seek(0)
        if width > max_width or height > max_height:
            raise ValidationError(_(f"Image dimensions must be at most {max_width}x{max_height} pixels."))
        return True
    except ValidationError:
        raise
    except Exception:
        logger.exception("Could not validate image dimensions")
        raise ValidationError(_("Invalid image file."))


def validate_url(url: str):
    validator = URLValidator()
    try:
        validator(url)
        return True
    except Exception:
        raise ValidationError(_("Invalid URL."))


HEX_COLOR_RE = re.compile(r"^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")


def validate_color_hex(color: str):
    if not color:
        raise ValidationError(_("Color cannot be empty"))
    if not HEX_COLOR_RE.match(color):
        raise ValidationError(_("Invalid HEX color. Expected formats: '#RRGGBB' or 'RRGGBB' or '#RGB'"))
    return True


def validate_json_structure(data: Any, schema: Dict[str, Any]):
    """
    Basic JSON structure validation: `schema` is a dict mapping keys to expected types
      e.g. {"name": str, "items": list, "metadata": dict}
    For complex validation, use jsonschema library.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            raise ValidationError(_("Invalid JSON string."))
    if not isinstance(data, dict):
        raise ValidationError(_("JSON payload must be an object."))
    for key, expected in schema.items():
        if key not in data:
            raise ValidationError(_(f"Missing key: {key}"))
        if expected is not None and not isinstance(data[key], expected):
            raise ValidationError(_(f"Invalid type for key {key}: expected {expected}"))
    return True
