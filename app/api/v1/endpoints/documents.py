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
    dependencies=[Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR]))],
    summary="Upload and Analyze Document",
    description="""
    Upload and analyze a document using AI.
    
    This endpoint:
    1. Validates file type (PDF, JPG, or PNG)
    2. Uploads file to AWS S3
    3. Uses AI (OpenAI GPT-4o) to classify the document:
       - **Invoice**: Documents with economic/financial data
       - **Information**: General text documents
    4. Extracts structured data based on classification:
       - **Invoice**: Client, provider, invoice number, date, products, total
       - **Information**: Description, summary, sentiment analysis
    5. Saves document and extracted data to database
    6. Logs events for audit trail
    
    **Authentication Required**: Yes (Bearer token)
    **Required Role**: user, admin, or moderator
    
    **Supported File Types**: PDF, JPG, JPEG, PNG
    """,
    response_description="Document analysis response with classification and extracted data",
    tags=["documents"]
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload and analyze (PDF, JPG, or PNG)"),
    current_user: Dict[str, Any] = Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR])),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Upload and analyze a document using AI.
    
    **Request**:
    - `file`: Document file (multipart/form-data)
      - Supported formats: PDF, JPG, JPEG, PNG
      - Maximum size: Configurable via server settings
    
    **Response**:
    - `document_id`: Database ID of the document
    - `filename`: Original filename
    - `file_type`: File type (PDF, JPG, PNG)
    - `s3_key`: S3 object key where file is stored
    - `classification`: Document classification (Invoice or Information)
    - `extracted_data`: Structured data based on classification
    - `uploaded_at`: Upload timestamp
    
    **Example Request** (multipart/form-data):
    ```
    file: invoice.pdf
    ```
    
    **Example Response (Invoice)**:
    ```json
    {
        "document_id": 1,
        "filename": "invoice.pdf",
        "file_type": "PDF",
        "s3_key": "documents/2024/12/invoice_1234567890.pdf",
        "classification": "Invoice",
        "extracted_data": {
            "client": {
                "name": "John Doe",
                "address": "123 Main St, City, State 12345"
            },
            "provider": {
                "name": "ABC Company Inc.",
                "address": "456 Business Ave, City, State 67890"
            },
            "invoice_number": "INV-2024-001",
            "date": "2024-12-06",
            "products": [
                {
                    "quantity": 2,
                    "name": "Product A",
                    "unit_price": 29.99,
                    "total": 59.98
                }
            ],
            "invoice_total": 59.98
        },
        "uploaded_at": "2024-12-06T10:30:00Z"
    }
    ```
    
    **Example Response (Information)**:
    ```json
    {
        "document_id": 2,
        "filename": "report.png",
        "file_type": "PNG",
        "s3_key": "documents/2024/12/report_1234567890.png",
        "classification": "Information",
        "extracted_data": {
            "description": "Meeting minutes from Q4 planning",
            "content_summary": "The meeting covered Q4 financial results...",
            "sentiment": "neutral"
        },
        "uploaded_at": "2024-12-06T10:30:00Z"
    }
    ```
    
    **Errors**:
    - `400 Bad Request`: Invalid file type, empty file, or AI processing failed
    - `401 Unauthorized`: Missing or invalid authentication token
    - `403 Forbidden`: Insufficient permissions
    - `500 Internal Server Error`: Database, S3, or AI service errors
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
        
        user_id = current_user.get("id_usuario")
        
        response = await upload_and_analyze_document(
            db=db,
            file_content=file_content,
            filename=file.filename,
            user_id=user_id
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

