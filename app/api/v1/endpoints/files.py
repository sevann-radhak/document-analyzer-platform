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
    status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: UploadFile = File(..., description="CSV file to upload"),
    param1: Optional[str] = Form(None, description="First additional parameter"),
    param2: Optional[str] = Form(None, description="Second additional parameter"),
    current_user: Dict[str, Any] = Depends(require_roles([UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR])),
    db: Session = Depends(get_db)
) -> FileUploadResponse:
    """
    Upload and validate a CSV file.
    
    Requires authentication and user role (user, admin, or moderator).
    The file is validated, uploaded to S3, and saved to the database.
    
    Returns validation results including empty values, incorrect types, and duplicates.
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

