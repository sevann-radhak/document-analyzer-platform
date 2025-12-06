"""Token renewal endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import RefreshTokenRequest, RefreshTokenResponse
from app.services.auth_service import refresh_token
from app.core.constants import ErrorMessages

router = APIRouter()


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK
)
async def refresh_access_token(
    request: RefreshTokenRequest
) -> RefreshTokenResponse:
    """
    Refresh a JWT access token.
    
    Validates the current token and generates a new one with extended expiration time.
    The token must not be expired to be refreshed.
    
    Returns a new access token with the same user data and extended expiration.
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

