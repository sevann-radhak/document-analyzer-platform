from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    pass


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class LoginResponse(BaseModel):
    id_usuario: int = Field(..., description="User ID")
    rol: str = Field(..., description="User role")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in minutes")


class RefreshTokenRequest(BaseModel):
    token: str = Field(..., description="Current JWT token to refresh")


class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="New token expiration time in minutes")

