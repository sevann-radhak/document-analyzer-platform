from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login_anonymous
from app.utils.database import get_db

router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    try:
        result = login_anonymous(db)
        return LoginResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during login: {str(e)}"
        )

