"""Document upload and analysis endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
from botocore.exceptions import ClientError, BotoCoreError

from app.schemas.document import DocumentResponse
from app.services.document_service import upload_and_analyze_document
from app.utils.database import get_db
from app.core.dependencies import require_roles
from app.core.constants import UserRoles, ErrorMessages

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR]))]
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload (PDF, JPG, or PNG)"),
    current_user: Dict[str, Any] = Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR])),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Upload and analyze a document using AI.
    
    Accepts PDF, JPG, or PNG files. The document is:
    1. Uploaded to S3
    2. Classified as Invoice or Information
    3. Analyzed to extract structured data
    4. Saved to database
    
    Requires authentication with user, admin, or moderator role.
    
    Returns classification and extracted data based on document type.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF, JPG, and PNG files are allowed. Received: {file_extension or 'unknown'}"
        )
    
    try:
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        response = await upload_and_analyze_document(
            db=db,
            file_content=file_content,
            filename=file.filename
        )
        
        return response
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AWS S3 error: {str(e)}"
        ) from e
    except BotoCoreError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AWS error: {str(e)}"
        ) from e
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during document processing: {str(e)}"
        ) from e

