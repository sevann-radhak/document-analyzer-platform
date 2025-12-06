"""Integration tests for authentication flow."""
import pytest
from fastapi import status


class TestLoginFlow:
    """Test cases for login endpoint."""
    
    def test_anonymous_login_returns_token(self, client):
        """Test that anonymous login returns a valid JWT token."""
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
    
    def test_anonymous_login_creates_user(self, client, test_db):
        """Test that anonymous login creates a new user in database."""
        from app.models.user import User
        
        initial_count = test_db.query(User).count()
        
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == status.HTTP_200_OK
        
        final_count = test_db.query(User).count()
        assert final_count == initial_count + 1
    
    def test_multiple_logins_create_multiple_users(self, client, test_db):
        """Test that multiple logins create multiple users."""
        from app.models.user import User
        
        response1 = client.post("/api/v1/auth/login", json={})
        response2 = client.post("/api/v1/auth/login", json={})
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        user_count = test_db.query(User).count()
        assert user_count >= 2
        
        assert response1.json()["id_usuario"] != response2.json()["id_usuario"]


class TestTokenRefreshFlow:
    """Test cases for token refresh endpoint."""
    
    def test_refresh_token_with_valid_token(self, client):
        """Test that token refresh works with a valid token."""
        login_response = client.post("/api/v1/auth/login", json={})
        assert login_response.status_code == status.HTTP_200_OK
        
        original_token = login_response.json()["access_token"]
        
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"token": original_token}
        )
        
        assert refresh_response.status_code == status.HTTP_200_OK
        data = refresh_response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
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

