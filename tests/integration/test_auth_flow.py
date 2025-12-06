"""Integration tests for authentication flow."""
from fastapi import status
from unittest.mock import patch
from app.core.security import create_access_token
from app.core.constants import UserRoles


class TestLoginFlow:
    """Test cases for anonymous login endpoint."""
    
    @patch('app.services.auth_service.create_anonymous_user')
    @patch('app.services.auth_service.create_access_token')
    def test_anonymous_login_returns_token(self, mock_create_token, mock_create_user, client, test_db):
        """Test that anonymous login returns a valid JWT token."""
        from app.models.user import User
        
        mock_user = User(id=1, rol=UserRoles.USER)
        mock_create_user.return_value = mock_user
        
        valid_token = create_access_token({"id_usuario": 1, "rol": UserRoles.USER})
        mock_create_token.return_value = valid_token
        
        response = client.post("/api/v1/auth/login", json={})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "id_usuario" in data
        assert "rol" in data
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        
        assert data["token_type"] == "bearer"
        assert isinstance(data["id_usuario"], int)
        assert data["rol"] in ["user", "admin", "moderator"]
        assert len(data["access_token"]) > 0


class TestTokenRefreshFlow:
    """Test cases for token refresh endpoint."""
    
    def test_refresh_token_with_invalid_token(self, client):
        """Test that refresh fails with an invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"token": "invalid_token"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_refresh_token_with_empty_token(self, client):
        """Test that refresh fails with an empty token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"token": ""}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('app.services.auth_service.create_access_token')
    def test_refresh_token_with_valid_token(self, mock_create_token, client):
        """Test that token refresh works with a valid token."""
        valid_token = create_access_token({"id_usuario": 1, "rol": UserRoles.USER})
        new_token = create_access_token({"id_usuario": 1, "rol": UserRoles.USER})
        mock_create_token.return_value = new_token
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"token": valid_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
