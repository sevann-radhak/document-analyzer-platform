from datetime import timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token, decode_access_token
from app.core.config import settings
from app.core.constants import UserRoles, TokenType, ErrorMessages


def create_anonymous_user(db: Session) -> User:
    """Create an anonymous user with default role."""
    user = User(rol=UserRoles.USER)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_anonymous(db: Session) -> Dict[str, Any]:
    """Perform anonymous login and return authentication response."""
    user = create_anonymous_user(db)
    
    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"id_usuario": user.id, "rol": user.rol},
        expires_delta=expires_delta
    )
    
    return {
        "id_usuario": user.id,
        "rol": user.rol,
        "access_token": access_token,
        "token_type": TokenType.BEARER,
        "expires_in": settings.jwt_expiration_minutes
    }


def refresh_token(token: str) -> Dict[str, Any]:
    """
    Refresh a JWT token if it is not expired.
    
    Args:
        token: Current JWT token to refresh
    
    Returns:
        Dictionary with new access token, token type, and expiration time
    
    Raises:
        ValueError: If token is expired, invalid, or missing required fields
    """
    payload = decode_access_token(token)
    
    if payload is None:
        raise ValueError(ErrorMessages.TOKEN_INVALID)
    
    if "id_usuario" not in payload or "rol" not in payload:
        raise ValueError(ErrorMessages.TOKEN_INVALID)
    
    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    new_token = create_access_token(
        data={"id_usuario": payload["id_usuario"], "rol": payload["rol"]},
        expires_delta=expires_delta
    )
    
    return {
        "access_token": new_token,
        "token_type": TokenType.BEARER,
        "expires_in": settings.jwt_expiration_minutes
    }

