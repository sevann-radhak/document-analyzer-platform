"""Token renewal endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import RefreshTokenRequest, RefreshTokenResponse
from app.services.auth_service import refresh_token
from app.core.constants import ErrorMessages

router = APIRouter()


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh JWT Token",
    description="""
    Refresh an existing JWT access token.
    
    This endpoint:
    - Validates the current token (must not be expired)
    - Extracts user ID and role from the token
    - Generates a new token with extended expiration time (15 minutes)
    - Returns the new token
    
    The token must be valid and not expired to be refreshed.
    """,
    response_description="New JWT token with extended expiration",
    tags=["authentication"]
)
async def refresh_access_token(
    request: RefreshTokenRequest
) -> RefreshTokenResponse:
    """
    Refresh a JWT access token.
    
    **Request Body**:
    - `token`: Current JWT token to refresh
    
    **Response**:
    - `access_token`: New JWT token with extended expiration
    - `token_type`: Always "bearer"
    - `expires_in`: New expiration time in minutes (15)
    
    **Example Request**:
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    **Example Response**:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 15
    }
    ```
    
    **Errors**:
    - `400 Bad Request`: Token is invalid, expired, or malformed
    - `500 Internal Server Error`: Unexpected error during token refresh
    """
    try:
        result = refresh_token(request.token)
        return RefreshTokenResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorMessages.TOKEN_REFRESH_ERROR
        ) from e

