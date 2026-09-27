"""Case upload validation constants and helpers."""

from __future__ import annotations

from pathlib import Path

import uuid

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def validate_upload(filename: str, mime_type: str, size: int) -> None:
    extension = Path(filename).suffix.casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file extension")
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported file MIME type")
    if size <= 0 or size > MAX_UPLOAD_BYTES:
        raise ValueError("File must be between 1 byte and 10 MB")


def safe_storage_name(original_filename: str) -> str:
    extension = Path(original_filename).suffix.casefold()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file extension")
    return f"{uuid.uuid4().hex}{extension}"
