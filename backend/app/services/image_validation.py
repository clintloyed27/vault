import hashlib
import io
import os
import re
from typing import Any, Optional, Tuple
from PIL import Image as PILImage, ImageOps

from app.core.config import settings
from app.core.exceptions import FileValidationError, PayloadTooLargeError


# Magic bytes signatures for robust MIME type detection
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}


def detect_mime_type(data: bytes) -> Optional[str]:
    """Detect real MIME type by inspecting leading byte signatures."""
    if len(data) < 12:
        return None

    for signature, mime in IMAGE_SIGNATURES.items():
        if data.startswith(signature):
            return mime

    # WebP signature: 'RIFF'....'WEBP'
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"

    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to strip directory traversal and dangerous characters."""
    clean = os.path.basename(filename.strip())
    # Remove control characters and non-printable characters
    clean = re.sub(r"[^\w\.\-\s_()]", "", clean)
    clean = re.sub(r"\s+", " ", clean)
    if not clean or clean.startswith("."):
        clean = f"image_{int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)}.jpg"
    return clean[:255]


def inspect_and_process_image(
    data: bytes, original_filename: str
) -> Tuple[bytes, bytes, int, int, str, str, dict[str, Any]]:
    """
    Validates payload, enforces MIME verification, strips sensitive EXIF,
    and creates an optimized WebP thumbnail.
    
    Returns:
        sanitized_image_bytes,
        thumbnail_bytes,
        width,
        height,
        mime_type,
        checksum_sha256,
        safe_metadata
    """
    # 1. Size check
    max_bytes = settings.STORAGE_MAX_FILE_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise PayloadTooLargeError(
            f"File size ({len(data)} bytes) exceeds maximum limit of {settings.STORAGE_MAX_FILE_SIZE_MB}MB"
        )

    # 2. Magic byte inspection
    detected_mime = detect_mime_type(data)
    if not detected_mime or detected_mime not in settings.ALLOWED_IMAGE_MIME_TYPES:
        raise FileValidationError(
            f"Unsupported or spoofed image payload. Allowed types: {', '.join(settings.ALLOWED_IMAGE_MIME_TYPES)}"
        )

    # 3. SHA-256 Checksum
    checksum = hashlib.sha256(data).hexdigest()

    # 4. Open with Pillow to verify image structure & integrity
    try:
        with io.BytesIO(data) as bio:
            with PILImage.open(bio) as img:
                img.verify()  # Verifies file integrity
    except Exception as e:
        raise FileValidationError(f"Corrupted or invalid image stream: {str(e)}")

    # 5. Re-open to process EXIF and generate thumbnail
    try:
        with io.BytesIO(data) as bio:
            with PILImage.open(bio) as img:
                # Correct orientation if EXIF orientation tag exists
                try:
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass

                width, height = img.size
                mime_format_map = {
                    "image/jpeg": "JPEG",
                    "image/png": "PNG",
                    "image/webp": "WEBP",
                    "image/gif": "GIF",
                }
                img_format = mime_format_map.get(detected_mime, "JPEG")

                # Extract basic safe metadata without GPS or camera serials
                safe_metadata = {
                    "format": img_format,
                    "mode": img.mode,
                    "width": width,
                    "height": height,
                }

                # Strip dangerous metadata by saving a sanitized copy
                sanitized_buffer = io.BytesIO()
                save_kwargs = {}
                if img_format == "JPEG":
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")
                    save_kwargs = {"quality": 95, "optimize": True}

                img.save(sanitized_buffer, format=img_format, **save_kwargs)
                sanitized_bytes = sanitized_buffer.getvalue()

                # Generate thumbnail (WebP 400x400)
                thumb_img = img.copy()
                thumb_img.thumbnail(settings.THUMBNAIL_MAX_SIZE, PILImage.Resampling.LANCZOS)
                if thumb_img.mode in ("RGBA", "LA") or (thumb_img.mode == "P" and "transparency" in thumb_img.info):
                    thumb_img = thumb_img.convert("RGBA")
                else:
                    thumb_img = thumb_img.convert("RGB")

                thumb_buffer = io.BytesIO()
                thumb_img.save(thumb_buffer, format="WEBP", quality=85)
                thumbnail_bytes = thumb_buffer.getvalue()

    except Exception as e:
        raise FileValidationError(f"Failed to process image payload: {str(e)}")

    return (
        sanitized_bytes,
        thumbnail_bytes,
        width,
        height,
        detected_mime,
        checksum,
        safe_metadata,
    )
