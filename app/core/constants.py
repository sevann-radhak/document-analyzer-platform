"""Application constants and messages."""
from typing import Final


class UserRoles:
    """User role constants."""
    USER: Final[str] = "user"
    ADMIN: Final[str] = "admin"
    MODERATOR: Final[str] = "moderator"


class TokenType:
    """Token type constants."""
    BEARER: Final[str] = "bearer"


class ValidationErrorType:
    """Validation error type constants."""
    EMPTY: Final[str] = "empty"
    INCORRECT_TYPE: Final[str] = "incorrect_type"
    DUPLICATE: Final[str] = "duplicate"


class ErrorMessages:
    """Centralized error messages."""
    
    # Database Configuration
    DB_SERVER_REQUIRED: Final[str] = "DB_SERVER must be set in .env file"
    DB_DATABASE_REQUIRED: Final[str] = "DB_DATABASE must be set in .env file"
    DB_USERNAME_REQUIRED: Final[str] = "DB_USERNAME must be set in .env file when not using Windows Authentication"
    DB_PASSWORD_REQUIRED: Final[str] = "DB_PASSWORD must be set in .env file when not using Windows Authentication"
    
    # AWS S3 Configuration
    S3_BUCKET_REQUIRED: Final[str] = "S3 bucket name must be configured in settings"
    AWS_ACCESS_KEY_REQUIRED: Final[str] = "AWS access key ID must be configured in settings"
    
    # AWS S3 Operations
    S3_UPLOAD_ERROR: Final[str] = "Boto3 error during file upload: {error}"
    S3_DOWNLOAD_ERROR: Final[str] = "Boto3 error during file download: {error}"
    S3_DELETE_ERROR: Final[str] = "Boto3 error during file deletion: {error}"
    S3_EXISTS_ERROR: Final[str] = "Boto3 error during file existence check: {error}"
    S3_PRESIGNED_URL_ERROR: Final[str] = "Boto3 error during presigned URL generation: {error}"
    S3_FILE_NOT_FOUND: Final[str] = "File {s3_key} not found in bucket"
    
    # Authentication
    INVALID_AUTH_CREDENTIALS: Final[str] = "Invalid authentication credentials"
    
    # API Errors
    DATABASE_ERROR_LOGIN: Final[str] = "Database error during login"
    UNEXPECTED_ERROR_LOGIN: Final[str] = "Unexpected error during login"
    TOKEN_EXPIRED: Final[str] = "Token has expired"
    TOKEN_INVALID: Final[str] = "Invalid or malformed token"
    TOKEN_REFRESH_ERROR: Final[str] = "Error refreshing token"
    
    # AI Service Configuration
    OPENAI_API_KEY_REQUIRED: Final[str] = "OpenAI API key must be configured in settings"
    
    # AI Service Operations
    AI_CLASSIFICATION_ERROR: Final[str] = "Error classifying document: {error}"
    AI_EXTRACTION_ERROR: Final[str] = "Error extracting data from document: {error}"
    AI_UNSUPPORTED_FILE_TYPE: Final[str] = "Unsupported file type: {file_type}. Supported types: PDF, JPG, PNG"
    AI_DOCUMENT_PROCESSING_ERROR: Final[str] = "Error processing document: {error}"


class ValidationMessages:
    """Centralized validation error messages."""
    
    FIELD_REQUIRED: Final[str] = "{field} field is required"
    EXPECTED_TYPE_GOT: Final[str] = "Expected {expected_type}, got {actual_type}"
    DUPLICATE_VALUE: Final[str] = "Duplicate {field} found"
    DUPLICATE_ID: Final[str] = "Duplicate ID found"


class ExcelExportConfig:
    """Configuration constants for Excel export functionality."""
    
    WORKSHEET_NAME: Final[str] = "Events"
    
    HEADER_EVENT_ID: Final[str] = "Event ID"
    HEADER_EVENT_TYPE: Final[str] = "Event Type"
    HEADER_DESCRIPTION: Final[str] = "Description"
    HEADER_USER_ID: Final[str] = "User ID"
    HEADER_CREATED_AT: Final[str] = "Created At"
    HEADER_UPDATED_AT: Final[str] = "Updated At"
    
    HEADER_BACKGROUND_COLOR: Final[str] = "366092"
    HEADER_TEXT_COLOR: Final[str] = "FFFFFF"
    HEADER_FONT_SIZE: Final[int] = 11
    
    BORDER_STYLE: Final[str] = "thin"
    
    COLUMN_WIDTH_EVENT_ID: Final[int] = 12
    COLUMN_WIDTH_EVENT_TYPE: Final[int] = 20
    COLUMN_WIDTH_DESCRIPTION: Final[int] = 80
    COLUMN_WIDTH_USER_ID: Final[int] = 12
    COLUMN_WIDTH_CREATED_AT: Final[int] = 20
    COLUMN_WIDTH_UPDATED_AT: Final[int] = 20
    
    DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
    
    ALIGNMENT_HORIZONTAL_CENTER: Final[str] = "center"
    ALIGNMENT_VERTICAL_CENTER: Final[str] = "center"
    ALIGNMENT_VERTICAL_TOP: Final[str] = "top"

