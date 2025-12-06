from typing import Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.core.constants import TokenType, ErrorMessages, UserRoles


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Extract and validate JWT token from request, returning user payload.
    
    FastAPI dependency that extracts the Bearer token from the Authorization header,
    validates it, and returns the decoded user payload. Raises 401 if token is invalid.
    
    Args:
        credentials: HTTPAuthorizationCredentials from FastAPI security dependency
        
    Returns:
        Dictionary containing user data from token (id_usuario, rol, exp, etc.)
        
    Raises:
        HTTPException: 401 Unauthorized if token is missing, invalid, or expired
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INVALID_AUTH_CREDENTIALS,
            headers={"WWW-Authenticate": TokenType.BEARER.capitalize()},
        )
    return payload


def require_roles(allowed_roles: List[str]):
    """
    Dependency factory for role-based access control.
    
    Creates a FastAPI dependency function that validates the user's role against
    a list of allowed roles. Raises 403 Forbidden if user's role is not in the list.
    
    Args:
        allowed_roles: List of allowed role names (e.g., [UserRoles.USER, UserRoles.ADMIN])
    
    Returns:
        FastAPI dependency function that:
            - Extracts current user from token (via get_current_user)
            - Validates user role is in allowed_roles
            - Returns user payload if authorized
            - Raises 403 if unauthorized
    
    Example:
        ```python
        @router.get("/admin")
        async def admin_endpoint(
            current_user: Dict = Depends(require_roles([UserRoles.ADMIN]))
        ):
            # Only admins can access this
            pass
        ```
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("rol", "")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
