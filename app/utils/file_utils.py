"""File utility functions for S3 key generation, file type detection, and MIME type mapping."""
import uuid
from typing import Callable, Optional
from datetime import datetime, timezone
from app.core.constants import FileConstants


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.
    
    Args:
        filename: File name with or without extension
    
    Returns:
        Lowercase file extension without dot, empty string if no extension
    """
    if "." not in filename:
        return ""
    return filename.lower().rsplit(".", 1)[-1]


def get_file_type(filename: str) -> str:
    """
    Get file type from filename extension.
    
    Args:
        filename: File name with extension
    
    Returns:
        File type (PDF, JPG, PNG, CSV) in uppercase, or extension in uppercase if unknown
    """
    extension = get_file_extension(filename)
    
    file_type_map = {
        "pdf": FileConstants.FILE_TYPE_PDF,
        "jpg": FileConstants.FILE_TYPE_JPG,
        "jpeg": FileConstants.FILE_TYPE_JPG,
        "png": FileConstants.FILE_TYPE_PNG,
        "csv": FileConstants.FILE_TYPE_CSV,
    }
    
    return file_type_map.get(extension, extension.upper() if extension else "")


def get_content_type(filename: str) -> str:
    """
    Get MIME content type for file upload.
    
    Args:
        filename: File name with extension
    
    Returns:
        MIME content type string
    """
    extension = get_file_extension(filename)
    
    mime_type_map = {
        "pdf": FileConstants.MIME_TYPE_PDF,
        "jpg": FileConstants.MIME_TYPE_JPEG,
        "jpeg": FileConstants.MIME_TYPE_JPEG,
        "png": FileConstants.MIME_TYPE_PNG,
        "csv": FileConstants.MIME_TYPE_CSV,
    }
    
    return mime_type_map.get(extension, FileConstants.MIME_TYPE_OCTET_STREAM)


def is_image_file(filename: str) -> bool:
    """
    Check if file is an image based on extension.
    
    Args:
        filename: File name with extension
    
    Returns:
        True if file is an image (JPG, JPEG, PNG), False otherwise
    """
    extension = get_file_extension(filename)
    return extension in FileConstants.SUPPORTED_IMAGE_EXTENSIONS


def is_document_file(filename: str) -> bool:
    """
    Check if file is a supported document type.
    
    Args:
        filename: File name with extension
    
    Returns:
        True if file is a supported document (PDF, JPG, JPEG, PNG), False otherwise
    """
    extension = get_file_extension(filename)
    return extension in FileConstants.SUPPORTED_DOCUMENT_EXTENSIONS


def generate_s3_key(
    filename: str,
    prefix: str,
    use_uuid: bool = False
) -> str:
    """
    Generate a unique S3 key for a file.
    
    Args:
        filename: Original filename
        prefix: S3 prefix (e.g., "uploads", "documents")
        use_uuid: If True, use UUID instead of timestamp for uniqueness
    
    Returns:
        S3 key in format: {prefix}/YYYY/MM/filename_timestamp.ext or filename_uuid.ext
    """
    now = datetime.now(timezone.utc)
    
    if use_uuid:
        unique_id = str(uuid.uuid4())[:8]
    else:
        unique_id = str(int(now.timestamp()))
    
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        safe_filename = f"{name}_{unique_id}.{ext}"
    else:
        safe_filename = f"{filename}_{unique_id}"
    
    if use_uuid:
        return f"{prefix}/{safe_filename}"
    
    return f"{prefix}/{now.year}/{now.month:02d}/{safe_filename}"


def resolve_s3_key_collision(
    filename: str,
    prefix: str,
    exists_checker: Callable[[str], bool],
    max_attempts: int = 10
) -> str:
    """
    Generate a unique S3 key, handling collisions by retrying with counter.
    
    Args:
        filename: Original filename
        prefix: S3 prefix (e.g., "uploads", "documents")
        exists_checker: Function that checks if S3 key exists (returns bool)
        max_attempts: Maximum number of collision resolution attempts
    
    Returns:
        Unique S3 key that doesn't exist
    
    Raises:
        ValueError: If unable to generate unique key after max_attempts
    """
    s3_key = generate_s3_key(filename, prefix)
    
    if not exists_checker(s3_key):
        return s3_key
    
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp())
    
    for counter in range(1, max_attempts + 1):
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            safe_filename = f"{name}_{timestamp}_{counter}.{ext}"
        else:
            safe_filename = f"{filename}_{timestamp}_{counter}"
        
        s3_key = f"{prefix}/{now.year}/{now.month:02d}/{safe_filename}"
        
        if not exists_checker(s3_key):
            return s3_key
    
    raise ValueError(
        f"Unable to generate unique S3 key after {max_attempts} attempts for file: {filename}"
    )

