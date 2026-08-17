"""Reusable file-upload + content validators."""
import os
import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_map_iframe(value):
    """Allow only a Google Maps embed iframe — blocks stored-XSS injection
    through this raw-HTML field by non-admin staff."""
    if not value:
        return
    if re.search(r"<script|javascript:|on\w+\s*=|<\s*img|data:", value, re.I):
        raise ValidationError("Only a Google Maps embed <iframe> is allowed here.")
    srcs = re.findall(r'src\s*=\s*["\']([^"\']+)["\']', value, re.I)
    for src in srcs:
        if not re.match(r"https://(www\.)?google\.com/maps/embed", src, re.I):
            raise ValidationError("The iframe src must be a Google Maps embed URL.")


def _validate_ext(value, allowed):
    ext = os.path.splitext(value.name)[1].lower().lstrip(".")
    if ext not in allowed:
        raise ValidationError(f"Unsupported file type '.{ext}'. Allowed: {', '.join(allowed)}.")


def _validate_size(value):
    limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if value.size > limit:
        raise ValidationError(f"File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB} MB.")


def validate_image(value):
    """Extension + size + verify the bytes are actually a raster image (Pillow).

    Defends against a non-image (e.g. an HTML/SVG payload) renamed to .png.
    """
    _validate_ext(value, settings.ALLOWED_IMAGE_EXTENSIONS)
    _validate_size(value)
    try:
        from PIL import Image
        pos = value.tell() if hasattr(value, "tell") else 0
        value.seek(0)
        Image.open(value).verify()
        value.seek(pos)
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("Uploaded file is not a valid image.")


def validate_document(value):
    """Extension + size + PDF magic-byte check (defends against renamed files)."""
    _validate_ext(value, settings.ALLOWED_DOC_EXTENSIONS)
    _validate_size(value)
    try:
        pos = value.tell() if hasattr(value, "tell") else 0
        value.seek(0)
        header = value.read(5)
        value.seek(pos)
    except Exception:
        raise ValidationError("Could not read the uploaded file.")
    if not header.startswith(b"%PDF-"):
        raise ValidationError("File does not appear to be a valid PDF.")
