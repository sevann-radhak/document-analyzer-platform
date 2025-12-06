from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class LoginRequest(BaseModel):
    """Request schema for anonymous login.
    
    No parameters required. Send empty JSON object.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {}
        }
    )


class TokenResponse(BaseModel):
    """Response schema for token operations."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c3VhcmlvIjoxLCJyb2wiOiJ1c2VyIiwiZXhwIjoxNzY1MDUwMzM5fQ.DjD8X8wHJx69TweDp-J2DJ2Z1vOIl0fgdo7XRDfrwRQ",
                "token_type": "bearer"
            }
        }
    )


class LoginResponse(BaseModel):
    """Response schema for login endpoint."""
    
    id_usuario: int = Field(..., description="User ID of the newly created user")
    rol: str = Field(..., description="User role (user, admin, or moderator)")
    access_token: str = Field(..., description="JWT access token for authentication")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")
    expires_in: int = Field(..., description="Token expiration time in minutes (default: 15)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_usuario": 1,
                "rol": "user",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c3VhcmlvIjoxLCJyb2wiOiJ1c2VyIiwiZXhwIjoxNzY1MDUwMzM5fQ.DjD8X8wHJx69TweDp-J2DJ2Z1vOIl0fgdo7XRDfrwRQ",
                "token_type": "bearer",
                "expires_in": 15
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    
    token: str = Field(..., description="Current JWT token to refresh")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c3VhcmlvIjoxLCJyb2wiOiJ1c2VyIiwiZXhwIjoxNzY1MDUwMzM5fQ.DjD8X8wHJx69TweDp-J2DJ2Z1vOIl0fgdo7XRDfrwRQ"
            }
        }
    )


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh endpoint."""
    
    access_token: str = Field(..., description="New JWT access token with extended expiration")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")
    expires_in: int = Field(..., description="New token expiration time in minutes (default: 15)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZF91c3VhcmlvIjoxLCJyb2wiOiJ1c2VyIiwiZXhwIjoxNzY1MDU1MzM5fQ.NewTokenSignatureHere",
                "token_type": "bearer",
                "expires_in": 15
            }
        }
    )

