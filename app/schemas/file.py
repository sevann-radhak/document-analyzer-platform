"""File upload and validation schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from app.core.constants import ValidationErrorType


class FileUploadRequest(BaseModel):
    """Request schema for file upload endpoint.
    
    Note: In FastAPI, file uploads use UploadFile from fastapi,
    and additional parameters are typically Form fields.
    This schema is for documentation purposes.
    """
    
    param1: Optional[str] = Field(None, description="First additional parameter")
    param2: Optional[str] = Field(None, description="Second additional parameter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "param1": "value1",
                "param2": "value2"
            }
        }


class ValidationError(BaseModel):
    """Schema for individual validation error."""
    
    row: int = Field(..., description="Row number where error occurred")
    column: str = Field(..., description="Column name where error occurred")
    error_type: str = Field(..., description=f"Type of error: '{ValidationErrorType.EMPTY}', '{ValidationErrorType.INCORRECT_TYPE}', or '{ValidationErrorType.DUPLICATE}'")
    message: str = Field(..., description="Human-readable error message")
    value: Optional[Any] = Field(None, description="The value that caused the error")


class ValidationResult(BaseModel):
    """Schema for file validation results."""
    
    is_valid: bool = Field(..., description="Whether the file passed all validations")
    total_rows: int = Field(..., description="Total number of rows in the file")
    total_errors: int = Field(..., description="Total number of validation errors found")
    empty_value_errors: List[ValidationError] = Field(
        default_factory=list,
        description="List of errors for empty values"
    )
    incorrect_type_errors: List[ValidationError] = Field(
        default_factory=list,
        description="List of errors for incorrect data types"
    )
    duplicate_errors: List[ValidationError] = Field(
        default_factory=list,
        description="List of errors for duplicate records"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": False,
                "total_rows": 100,
                "total_errors": 5,
                "empty_value_errors": [
                    {
                        "row": 3,
                        "column": "email",
                        "error_type": ValidationErrorType.EMPTY,
                        "message": "Email field is required",
                        "value": None
                    }
                ],
                "incorrect_type_errors": [
                    {
                        "row": 5,
                        "column": "age",
                        "error_type": ValidationErrorType.INCORRECT_TYPE,
                        "message": "Expected integer, got string",
                        "value": "twenty"
                    }
                ],
                "duplicate_errors": [
                    {
                        "row": 10,
                        "column": "id",
                        "error_type": ValidationErrorType.DUPLICATE,
                        "message": "Duplicate ID found",
                        "value": 123
                    }
                ]
            }
        }


class FileUploadResponse(BaseModel):
    """Response schema for file upload endpoint."""
    
    file_id: int = Field(..., description="ID of the uploaded file record in database")
    filename: str = Field(..., description="Original filename")
    s3_key: str = Field(..., description="S3 object key where file is stored")
    uploaded_at: datetime = Field(..., description="Timestamp when file was uploaded")
    validation_results: ValidationResult = Field(..., description="File validation results")
    param1: Optional[str] = Field(None, description="First additional parameter value")
    param2: Optional[str] = Field(None, description="Second additional parameter value")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": 1,
                "filename": "data.csv",
                "s3_key": "uploads/2024/12/data.csv",
                "uploaded_at": "2024-12-06T10:30:00Z",
                "validation_results": {
                    "is_valid": True,
                    "total_rows": 100,
                    "total_errors": 0,
                    "empty_value_errors": [],
                    "incorrect_type_errors": [],
                    "duplicate_errors": []
                },
                "param1": "value1",
                "param2": "value2"
            }
        }

