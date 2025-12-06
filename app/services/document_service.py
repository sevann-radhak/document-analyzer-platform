"""Document service for handling document uploads, AI analysis, and storage."""
import io
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError, BotoCoreError

from app.repositories.document_repository import DocumentRepository
from app.utils.aws_client import S3Client, get_s3_client
from app.services.ai_service import AIServiceInterface, DocumentClassification
from app.services.openai_service import OpenAIService
from app.schemas.document import DocumentResponse, InvoiceData, InformationData
from app.core.constants import ErrorMessages


def generate_document_s3_key(filename: str) -> str:
    """
    Generate a unique S3 key for a document.
    
    Args:
        filename: Original filename
    
    Returns:
        S3 key in format: documents/YYYY/MM/filename_timestamp.ext
    """
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp())
    
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        safe_filename = f"{name}_{timestamp}.{ext}"
    else:
        safe_filename = f"{filename}_{timestamp}"
    
    return f"documents/{now.year}/{now.month:02d}/{safe_filename}"


def get_file_type(filename: str) -> str:
    """
    Get file type from filename extension.
    
    Args:
        filename: File name with extension
    
    Returns:
        File type (PDF, JPG, PNG) in uppercase
    """
    extension = filename.lower().split('.')[-1]
    file_types = {
        'pdf': 'PDF',
        'jpg': 'JPG',
        'jpeg': 'JPG',
        'png': 'PNG'
    }
    return file_types.get(extension, extension.upper())


def get_content_type(filename: str) -> str:
    """
    Get content type for file upload.
    
    Args:
        filename: File name with extension
    
    Returns:
        MIME content type
    """
    extension = filename.lower().split('.')[-1]
    content_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png'
    }
    return content_types.get(extension, 'application/octet-stream')


async def upload_and_analyze_document(
    db: Session,
    file_content: bytes,
    filename: str,
    ai_service: Optional[AIServiceInterface] = None
) -> DocumentResponse:
    """
    Upload and analyze a document using AI.
    
    This function:
    1. Validates file type (PDF, JPG, PNG)
    2. Uploads file to S3
    3. Uses AI service to classify and extract data
    4. Saves document record to database
    5. Returns analysis results
    
    Args:
        db: Database session
        file_content: Document file content as bytes
        filename: Original filename
        ai_service: AI service instance (defaults to OpenAIService)
    
    Returns:
        DocumentResponse with document details and extracted data
    
    Raises:
        ValueError: If file type is invalid or AI processing fails
        Exception: If S3 upload or database save fails
    """
    file_type = get_file_type(filename)
    
    if file_type not in ['PDF', 'JPG', 'PNG']:
        raise ValueError(
            ErrorMessages.AI_UNSUPPORTED_FILE_TYPE.format(file_type=file_type)
        )
    
    if ai_service is None:
        ai_service = OpenAIService()
    
    s3_client = get_s3_client()
    document_repo = DocumentRepository(db)
    
    s3_key = generate_document_s3_key(filename)
    
    counter = 0
    while document_repo.exists_by_s3_key(s3_key):
        counter += 1
        now = datetime.now(timezone.utc)
        timestamp = int(now.timestamp())
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            safe_filename = f"{name}_{timestamp}_{counter}.{ext}"
        else:
            safe_filename = f"{filename}_{timestamp}_{counter}"
        s3_key = f"documents/{now.year}/{now.month:02d}/{safe_filename}"
    
    file_obj = io.BytesIO(file_content)
    content_type = get_content_type(filename)
    
    try:
        s3_client.upload_file(
            file_obj=file_obj,
            s3_key=s3_key,
            content_type=content_type
        )
    except (ClientError, BotoCoreError) as e:
        raise ValueError(
            ErrorMessages.S3_UPLOAD_ERROR.format(error=str(e))
        ) from e
    
    try:
        analysis_result = await ai_service.analyze_document(
            file_content=file_content,
            filename=filename
        )
    except ValueError as e:
        raise ValueError(
            ErrorMessages.AI_DOCUMENT_PROCESSING_ERROR.format(error=str(e))
        ) from e
    
    classification = analysis_result["classification"]
    extracted_data_raw = analysis_result["extracted_data"]
    
    if classification == DocumentClassification.INVOICE:
        extracted_data = InvoiceData(**extracted_data_raw)
    else:
        extracted_data = InformationData(**extracted_data_raw)
    
    document_record = document_repo.create(
        filename=filename,
        file_type=file_type,
        s3_key=s3_key,
        classification=classification.value,
        extracted_data=extracted_data_raw
    )
    
    return DocumentResponse(
        document_id=document_record.id,
        filename=document_record.filename,
        file_type=document_record.file_type,
        s3_key=document_record.s3_key,
        classification=classification,
        extracted_data=extracted_data,
        uploaded_at=document_record.created_at
    )

