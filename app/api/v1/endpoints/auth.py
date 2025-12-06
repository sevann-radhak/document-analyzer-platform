from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login_anonymous
from app.utils.database import get_db

router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """Anonymous login endpoint - creates a new user and returns JWT token."""
    try:
        result = login_anonymous(db)
        return LoginResponse(**result)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during login"
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during login"
        ) from e

