"""Global exception handlers for the application."""
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from botocore.exceptions import ClientError, BotoCoreError

from app.core.exceptions import (
    BaseAPIException,
    DatabaseException,
    AuthenticationException,
    AuthorizationException,
    ValidationException,
    NotFoundException,
    ExternalServiceException,
    BusinessLogicException
)
from app.core.config import settings


async def base_api_exception_handler(
    request: Request,
    exc: BaseAPIException
) -> JSONResponse:
    """Handle BaseAPIException and its subclasses."""
    response_data = {
        "error": {
            "message": exc.detail,
            "code": exc.error_code or "API_ERROR",
            "status_code": exc.status_code
        }
    }
    
    if settings.debug and hasattr(exc, "__cause__") and exc.__cause__:
        response_data["error"]["cause"] = str(exc.__cause__)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation failed",
                "code": "VALIDATION_ERROR",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "errors": errors
            }
        }
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    error_message = "Database operation failed"
    
    if settings.debug:
        error_message = f"Database error: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": error_message,
                "code": "DATABASE_ERROR",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        }
    )


async def boto_exception_handler(
    request: Request,
    exc: Union[ClientError, BotoCoreError]
) -> JSONResponse:
    """Handle AWS Boto3 errors."""
    error_code = "AWS_ERROR"
    error_message = "External service error"
    
    if isinstance(exc, ClientError):
        error_code = exc.response.get("Error", {}).get("Code", "AWS_CLIENT_ERROR")
        error_message = exc.response.get("Error", {}).get("Message", "AWS service error")
    
    if settings.debug:
        error_message = f"AWS error: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": {
                "message": error_message,
                "code": error_code,
                "status_code": status.HTTP_502_BAD_GATEWAY,
                "service": "AWS"
            }
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    error_message = "An unexpected error occurred"
    
    if settings.debug:
        error_message = f"Unexpected error: {str(exc)}"
        import traceback
        error_message += f"\n{traceback.format_exc()}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": error_message,
                "code": "INTERNAL_SERVER_ERROR",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        }
    )

