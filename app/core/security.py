from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError
from app.core.config import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with optional expiration delta.
    
    Encodes user data (id_usuario, rol, etc.) into a JWT token with expiration time.
    Uses the configured secret key and algorithm from settings.
    
    Args:
        data: Dictionary containing user data to encode (e.g., id_usuario, rol)
        expires_delta: Optional custom expiration time delta. If not provided,
                      uses default expiration from settings (15 minutes)
    
    Returns:
        Encoded JWT token string
        
    Raises:
        Exception: If token encoding fails
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.
    
    Verifies the token signature, expiration, and returns the payload if valid.
    Returns None if the token is invalid, expired, or malformed.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Dictionary containing token payload (id_usuario, rol, exp, etc.) if valid,
        None if token is invalid, expired, or malformed
        
    Note:
        This function silently handles all token errors and returns None.
        Use this for validation; raise exceptions in higher-level functions if needed.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except InvalidTokenError:
        return None


