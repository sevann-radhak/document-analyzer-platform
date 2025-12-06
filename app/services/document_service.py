"""Document service for handling document uploads, AI analysis, and storage."""
import io
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError, BotoCoreError

from app.repositories.document_repository import DocumentRepository
from app.utils.aws_client import S3Client, get_s3_client
from app.utils.file_utils import (
    get_file_type,
    get_content_type,
    is_document_file,
    resolve_s3_key_collision
)
from app.services.ai_service import AIServiceInterface, DocumentClassification
from app.services.openai_service import OpenAIService
from app.services.event_service import log_document_upload, log_ai_classification
from app.schemas.document import DocumentResponse, InvoiceData, InformationData
from app.core.constants import ErrorMessages, FileConstants
from app.core.logging_config import get_logger
from app.utils.logger import log_event

logger = get_logger(__name__)


async def upload_and_analyze_document(
    db: Session,
    file_content: bytes,
    filename: str,
    ai_service: Optional[AIServiceInterface] = None,
    user_id: Optional[int] = None
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
    if not is_document_file(filename):
        file_type = get_file_type(filename)
        raise ValueError(
            ErrorMessages.AI_UNSUPPORTED_FILE_TYPE.format(file_type=file_type)
        )
    
    file_type = get_file_type(filename)
    
    if ai_service is None:
        ai_service = OpenAIService()
    
    s3_client = get_s3_client()
    document_repo = DocumentRepository(db)
    
    s3_key = resolve_s3_key_collision(
        filename=filename,
        prefix=FileConstants.S3_PREFIX_DOCUMENTS,
        exists_checker=document_repo.exists_by_s3_key
    )
    
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
    
    try:
        log_ai_classification(
            db=db,
            filename=filename,
            classification=classification.value,
            user_id=user_id
        )
    except Exception as e:
        logger.warning(
            f"Failed to log AI classification event: {str(e)}",
            extra={"document_filename": filename, "classification": classification.value}
        )
    
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
    
    log_event(
        logger=logger,
        level=logging.INFO,
        message=f"Document analyzed: {filename} -> {classification.value}",
        document_id=document_record.id,
        user_id=user_id,
        extra={
            "filename": filename,
            "file_type": file_type,
            "classification": classification.value,
            "s3_key": s3_key
        }
    )
    
    try:
        log_document_upload(
            db=db,
            filename=filename,
            classification=classification.value,
            document_id=document_record.id,
            user_id=user_id
        )
    except Exception as e:
        logger.warning(
            f"Failed to log document upload event: {str(e)}",
            extra={
                "document_filename": filename,
                "document_id": document_record.id,
                "classification": classification.value
            }
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

