"""File upload endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any
from app.schemas.file import FileUploadResponse
from app.services.file_service import upload_csv_file
from app.utils.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.constants import ErrorMessages, UserRoles
from botocore.exceptions import ClientError, BotoCoreError

router = APIRouter()


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload CSV File",
    description="""
    Upload and validate a CSV file.
    
    This endpoint:
    1. Validates the CSV file format and content
    2. Checks for empty values, incorrect types, and duplicates
    3. Uploads the file to AWS S3
    4. Saves file metadata to the database
    5. Returns validation results
    
    **Authentication Required**: Yes (Bearer token)
    **Required Role**: user, admin, or moderator
    
    **File Requirements**:
    - File type: CSV only
    - File must not be empty
    - File must have valid CSV structure
    """,
    response_description="File upload response with validation results",
    tags=["files"]
)
async def upload_file(
    file: UploadFile = File(..., description="CSV file to upload and validate"),
    param1: Optional[str] = Form(None, description="First additional parameter (optional)"),
    param2: Optional[str] = Form(None, description="Second additional parameter (optional)"),
    current_user: Dict[str, Any] = Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR])),
    db: Session = Depends(get_db)
) -> FileUploadResponse:
    """
    Upload and validate a CSV file.
    
    **Request**:
    - `file`: CSV file (multipart/form-data)
    - `param1`: Optional first parameter
    - `param2`: Optional second parameter
    
    **Response**:
    - `file_id`: Database ID of the uploaded file
    - `filename`: Original filename
    - `s3_key`: S3 object key where file is stored
    - `uploaded_at`: Upload timestamp
    - `validation_results`: Detailed validation results
    - `param1`, `param2`: Echoed parameter values
    
    **Example Request** (multipart/form-data):
    ```
    file: data.csv
    param1: value1
    param2: value2
    ```
    
    **Example Response**:
    ```json
    {
        "file_id": 1,
        "filename": "data.csv",
        "s3_key": "uploads/2024/12/data_1234567890.csv",
        "uploaded_at": "2024-12-06T10:30:00Z",
        "validation_results": {
            "is_valid": true,
            "total_rows": 100,
            "total_errors": 0,
            "empty_value_errors": [],
            "incorrect_type_errors": [],
            "duplicate_errors": []
        },
        "param1": "value1",
        "param2": "value2"
    }
    ```
    
    **Errors**:
    - `400 Bad Request`: Invalid file type, empty file, or validation errors
    - `401 Unauthorized`: Missing or invalid authentication token
    - `403 Forbidden`: Insufficient permissions
    - `500 Internal Server Error`: Database or S3 errors
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    try:
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        user_id = current_user.get("id_usuario")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        
        response = upload_csv_file(
            db=db,
            file_content=file_content,
            filename=file.filename,
            uploaded_by=user_id,
            param1=param1,
            param2=param2
        )
        
        return response
    
    except HTTPException:
        raise
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        ) from e

