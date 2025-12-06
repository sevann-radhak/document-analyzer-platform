"""Custom exception classes for the application."""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class DatabaseException(BaseAPIException):
    """Exception for database-related errors."""
    
    def __init__(
        self,
        detail: str = "Database operation failed",
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
            error_code=error_code or "DATABASE_ERROR"
        )


class AuthenticationException(BaseAPIException):
    """Exception for authentication errors."""
    
    def __init__(
        self,
        detail: str = "Authentication failed",
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
            error_code=error_code or "AUTHENTICATION_ERROR"
        )


class AuthorizationException(BaseAPIException):
    """Exception for authorization errors."""
    
    def __init__(
        self,
        detail: str = "Access denied",
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
            error_code=error_code or "AUTHORIZATION_ERROR"
        )


class ValidationException(BaseAPIException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        detail: str = "Validation failed",
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
            error_code=error_code or "VALIDATION_ERROR"
        )


class NotFoundException(BaseAPIException):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        detail: str = "Resource not found",
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
            error_code=error_code or "NOT_FOUND"
        )


class ExternalServiceException(BaseAPIException):
    """Exception for external service errors (S3, AI, etc.)."""
    
    def __init__(
        self,
        detail: str = "External service error",
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
        service: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            headers=headers,
            error_code=error_code or "EXTERNAL_SERVICE_ERROR"
        )
        self.service = service


class BusinessLogicException(BaseAPIException):
    """Exception for business logic errors."""
    
    def __init__(
        self,
        detail: str = "Business logic error",
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers,
            error_code=error_code or "BUSINESS_LOGIC_ERROR"
        )

