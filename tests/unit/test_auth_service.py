import pytest
from datetime import timedelta
from unittest.mock import patch
from app.services.auth_service import create_anonymous_user, login_anonymous
from app.models.user import User
from app.core.config import settings
from app.core.constants import UserRoles, TokenType
from tests.unit.conftest import mock_db, sample_user, admin_user, mock_create_anonymous_user, mock_create_access_token


class TestCreateAnonymousUser:
    """Test cases for create_anonymous_user function."""
    
    def test_create_anonymous_user_creates_user_with_default_rol(self, mock_db, sample_user):
        """Test that anonymous user is created with default 'user' role."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            result = create_anonymous_user(mock_db)
            
            assert result.rol == UserRoles.USER
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(result)
    
    def test_create_anonymous_user_calls_db_add(self, mock_db, sample_user):
        """Test that db.add is called with the user."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            result = create_anonymous_user(mock_db)
            
            mock_db.add.assert_called_once_with(result)
    
    def test_create_anonymous_user_calls_db_commit(self, mock_db, sample_user):
        """Test that db.commit is called after adding user."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            create_anonymous_user(mock_db)
            
            mock_db.commit.assert_called_once()
    
    def test_create_anonymous_user_calls_db_refresh(self, mock_db, sample_user):
        """Test that db.refresh is called with the created user."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            result = create_anonymous_user(mock_db)
            
            mock_db.refresh.assert_called_once_with(result)
    
    def test_create_anonymous_user_returns_user_instance(self, mock_db, sample_user):
        """Test that function returns a User instance."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            result = create_anonymous_user(mock_db)
            
            assert isinstance(result, User)
            assert result.id == 1
            assert result.rol == UserRoles.USER
    
    def test_create_anonymous_user_handles_db_commit_error(self, mock_db, sample_user):
        """Test that function handles database commit errors."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            mock_db.commit.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                create_anonymous_user(mock_db)
    
    def test_create_anonymous_user_handles_db_add_error(self, mock_db, sample_user):
        """Test that function handles database add errors."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            mock_db.add.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                create_anonymous_user(mock_db)
    
    def test_create_anonymous_user_handles_db_refresh_error(self, mock_db, sample_user):
        """Test that function handles database refresh errors."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            mock_db.refresh.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                create_anonymous_user(mock_db)
    
    def test_create_anonymous_user_logs_user_creation(self, mock_db, sample_user):
        """Test that function logs user creation."""
        with patch('app.services.auth_service.User', return_value=sample_user), \
             patch('app.services.auth_service.logger') as mock_logger:
            create_anonymous_user(mock_db)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Anonymous user created" in call_args[0][0] or "user_id" in call_args[1].get("extra", {})
    
    def test_create_anonymous_user_creates_user_with_correct_attributes(self, mock_db, sample_user):
        """Test that created user has correct attributes."""
        with patch('app.services.auth_service.User', return_value=sample_user):
            result = create_anonymous_user(mock_db)
            
            assert hasattr(result, 'id')
            assert hasattr(result, 'rol')
            assert result.rol == UserRoles.USER


class TestLoginAnonymous:
    """Test cases for login_anonymous function."""
    
    def test_login_anonymous_creates_user(self, mock_db, sample_user, mock_create_access_token):
        """Test that login_anonymous creates a new user."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user):
            result = login_anonymous(mock_db)
            
            assert result["id_usuario"] == sample_user.id
    
    def test_login_anonymous_returns_correct_user_id(self, mock_db, sample_user, mock_create_access_token):
        """Test that login_anonymous returns correct user ID."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user):
            result = login_anonymous(mock_db)
            
            assert result["id_usuario"] == 1
    
    def test_login_anonymous_returns_correct_rol(self, mock_db, sample_user, mock_create_access_token):
        """Test that login_anonymous returns correct role."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user):
            result = login_anonymous(mock_db)
            
            assert result["rol"] == UserRoles.USER
    
    def test_login_anonymous_returns_access_token(self, mock_db, sample_user):
        """Test that login_anonymous returns an access token."""
        test_token = "test_jwt_token_12345"
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user), \
             patch('app.services.auth_service.create_access_token', return_value=test_token):
            result = login_anonymous(mock_db)
            
            assert result["access_token"] == test_token
    
    def test_login_anonymous_returns_token_type(self, mock_db, sample_user, mock_create_access_token):
        """Test that login_anonymous returns correct token type."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user):
            result = login_anonymous(mock_db)
            
            assert result["token_type"] == TokenType.BEARER
    
    def test_login_anonymous_returns_expires_in(self, mock_db, sample_user, mock_create_access_token):
        """Test that login_anonymous returns correct expiration time."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user):
            result = login_anonymous(mock_db)
            
            assert result["expires_in"] == settings.jwt_expiration_minutes
    
    def test_login_anonymous_calls_create_access_token_with_correct_data(self, mock_db, sample_user):
        """Test that create_access_token is called with correct user data."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user), \
             patch('app.services.auth_service.create_access_token') as mock_create_token:
            login_anonymous(mock_db)
            
            mock_create_token.assert_called_once()
            call_args = mock_create_token.call_args
            assert call_args[1]["data"]["id_usuario"] == sample_user.id
            assert call_args[1]["data"]["rol"] == sample_user.rol
            assert isinstance(call_args[1]["expires_delta"], timedelta)
    
    def test_login_anonymous_uses_correct_expiration_delta(self, mock_db, sample_user):
        """Test that login_anonymous uses correct expiration delta from settings."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user), \
             patch('app.services.auth_service.create_access_token') as mock_create_token:
            login_anonymous(mock_db)
            
            call_args = mock_create_token.call_args
            expires_delta = call_args[1]["expires_delta"]
            assert expires_delta == timedelta(minutes=settings.jwt_expiration_minutes)
    
    def test_login_anonymous_returns_complete_response_structure(self, mock_db, sample_user, mock_create_access_token):
        """Test that login_anonymous returns all required fields."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user):
            result = login_anonymous(mock_db)
            
            required_fields = ["id_usuario", "rol", "access_token", "token_type", "expires_in"]
            for field in required_fields:
                assert field in result
    
    def test_login_anonymous_handles_different_user_roles(self, mock_db, admin_user, mock_create_access_token):
        """Test that login_anonymous works with different user roles."""
        with patch('app.services.auth_service.create_anonymous_user', return_value=admin_user):
            result = login_anonymous(mock_db)
            
            assert result["rol"] == UserRoles.ADMIN
            assert result["id_usuario"] == 2

