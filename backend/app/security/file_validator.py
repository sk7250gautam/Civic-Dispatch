"""
Civic Dispatch — Secure File Upload Validator & Storage Handler
Enforces strict MIME validation, magic-byte inspection, path traversal prevention,
and metadata sanitization.
"""

import os
import uuid
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB

class FileValidationError(Exception):
    pass

def validate_and_save_upload(
    file_storage,
    upload_folder: str,
    strip_exif: bool = True
) -> Tuple[str, str, int, str, Optional[Dict[str, float]]]:
    """
    Validates uploaded image and stores securely with a randomized UUID filename.
    Returns: (saved_relative_path, original_filename, file_size, mime_type, extracted_gps)
    """
    if not file_storage or not file_storage.filename:
        raise FileValidationError("No file uploaded or filename is empty.")

    original_filename = secure_filename(file_storage.filename)
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(f"Disallowed file extension '{extension}'. Permitted: {', '.join(ALLOWED_EXTENSIONS)}")

    # Check content size
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise FileValidationError(f"File exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024*1024)} MB.")

    if file_size == 0:
        raise FileValidationError("Empty file uploaded.")

    # Inspect Magic Bytes / Image Validity using Pillow
    extracted_gps = None
    try:
        image = Image.open(file_storage)
        image.verify()  # Verifies file integrity
    except Exception as e:
        raise FileValidationError(f"Corrupted or invalid image file: {str(e)}")

    # Re-open after verify() to inspect metadata/save
    file_storage.seek(0)
    image = Image.open(file_storage)

    # Detect actual MIME
    detected_format = (image.format or "").upper()
    mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    mime_type = mime_map.get(detected_format)
    if not mime_type or mime_type not in ALLOWED_MIMES:
        raise FileValidationError(f"Unsafe image format '{detected_format}'. Only JPEG, PNG, WEBP are accepted.")

    # Optional EXIF GPS Extraction
    try:
        exif = image.getexif()
        if exif:
            extracted_gps = _extract_gps_from_exif(exif)
    except Exception:
        extracted_gps = None

    # Generate secure random UUID filename
    safe_filename = f"{uuid.uuid4().hex}{extension}"
    upload_path = Path(upload_folder)
    upload_path.mkdir(parents=True, exist_ok=True)
    destination = upload_path / safe_filename

    # Save image (with EXIF stripped if requested)
    if strip_exif:
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        image_without_exif.save(destination, format=detected_format)
    else:
        file_storage.seek(0)
        file_storage.save(str(destination))

    return safe_filename, original_filename, file_size, mime_type, extracted_gps

def _extract_gps_from_exif(exif) -> Optional[Dict[str, float]]:
    """Parses raw EXIF tags for GPS coordinates."""
    try:
        gps_info = {}
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                gps_info = value
                break

        if not gps_info:
            return None

        # Helper to convert degrees/minutes/seconds tuple
        def _convert_to_degrees(value):
            d, m, s = value
            return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)

        lat = _convert_to_degrees(gps_info[2])
        if gps_info[1] == "S":
            lat = -lat

        lon = _convert_to_degrees(gps_info[4])
        if gps_info[3] == "W":
            lon = -lon

        return {"latitude": round(lat, 6), "longitude": round(lon, 6)}
    except Exception:
        return None
