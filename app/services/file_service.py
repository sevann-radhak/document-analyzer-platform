"""File service for handling file uploads, validation, and storage."""
import io
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.file_repository import FileRepository
from app.utils.aws_client import S3Client, get_s3_client
from app.utils.validators import CSVValidator, validate_csv
from app.schemas.file import FileUploadResponse, ValidationResult
from app.models.file import File


def generate_s3_key(filename: str) -> str:
    """
    Generate a unique S3 key for a file.
    
    Args:
        filename: Original filename
    
    Returns:
        S3 key in format: uploads/YYYY/MM/filename_timestamp.ext
    """
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp())
    
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        safe_filename = f"{name}_{timestamp}.{ext}"
    else:
        safe_filename = f"{filename}_{timestamp}"
    
    return f"uploads/{now.year}/{now.month:02d}/{safe_filename}"


def upload_csv_file(
    db: Session,
    file_content: bytes,
    filename: str,
    uploaded_by: int,
    param1: Optional[str] = None,
    param2: Optional[str] = None,
    required_columns: Optional[list] = None,
    column_types: Optional[Dict[str, type]] = None,
    unique_columns: Optional[list] = None
) -> FileUploadResponse:
    """
    Upload and validate a CSV file.
    
    This function:
    1. Validates the CSV file
    2. Uploads file to S3
    3. Saves file record to database
    4. Returns validation results
    
    Args:
        db: Database session
        file_content: CSV file content as bytes
        filename: Original filename
        uploaded_by: ID of user uploading the file
        param1: First additional parameter (optional)
        param2: Second additional parameter (optional)
        required_columns: List of required column names for validation
        column_types: Dictionary mapping column names to expected types
        unique_columns: List of column names that must be unique
    
    Returns:
        FileUploadResponse with file details and validation results
    
    Raises:
        ValueError: If file validation fails critically
        Exception: If S3 upload or database save fails
    """
    s3_client = get_s3_client()
    file_repo = FileRepository(db)
    
    s3_key = generate_s3_key(filename)
    
    counter = 0
    while file_repo.exists_by_s3_key(s3_key):
        counter += 1
        now = datetime.now(timezone.utc)
        timestamp = int(now.timestamp())
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            safe_filename = f"{name}_{timestamp}_{counter}.{ext}"
        else:
            safe_filename = f"{filename}_{timestamp}_{counter}"
        s3_key = f"uploads/{now.year}/{now.month:02d}/{safe_filename}"
    
    validation_result = validate_csv(
        file_content=file_content,
        required_columns=required_columns,
        column_types=column_types,
        unique_columns=unique_columns
    )
    
    file_obj = io.BytesIO(file_content)
    s3_client.upload_file(
        file_obj=file_obj,
        s3_key=s3_key,
        content_type="text/csv"
    )
    
    validation_results_dict = validation_result.model_dump()
    
    file_record = file_repo.create(
        filename=filename,
        s3_key=s3_key,
        uploaded_by=uploaded_by,
        validation_results=validation_results_dict
    )
    
    return FileUploadResponse(
        file_id=file_record.id,
        filename=file_record.filename,
        s3_key=file_record.s3_key,
        uploaded_at=file_record.created_at,
        validation_results=validation_result,
        param1=param1,
        param2=param2
    )

