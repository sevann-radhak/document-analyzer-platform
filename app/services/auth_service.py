from datetime import timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import create_access_token, decode_access_token
from app.core.config import settings
from app.core.constants import UserRoles, TokenType, ErrorMessages
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def create_anonymous_user(db: Session) -> User:
    """
    Create an anonymous user with default role.
    
    This function creates a new user in the database with the default USER role.
    Anonymous users are created automatically when users login without credentials.
    
    Args:
        db: SQLAlchemy database session
        
    Returns:
        Created User object with assigned ID and default role
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    user = User(rol=UserRoles.USER)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Anonymous user created", extra={"user_id": user.id, "role": user.rol})
    return user


def login_anonymous(db: Session) -> Dict[str, Any]:
    """
    Perform anonymous login and return authentication response.
    
    This function creates an anonymous user (if needed) and generates a JWT token
    with user ID, role, and expiration time. No credentials are required.
    
    Args:
        db: SQLAlchemy database session
        
    Returns:
        Dictionary containing:
            - id_usuario: User ID
            - rol: User role
            - access_token: JWT token string
            - token_type: Token type (Bearer)
            - expires_in: Token expiration time in minutes
        
    Raises:
        SQLAlchemyError: If database operation fails
        Exception: If token generation fails
    """
    user = create_anonymous_user(db)

    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"id_usuario": user.id, "rol": user.rol},
        expires_delta=expires_delta
    )
    
    logger.info(
        "Anonymous login successful",
        extra={"user_id": user.id, "role": user.rol, "expires_in": settings.jwt_expiration_minutes}
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

