import pytest
from datetime import timedelta, datetime, timezone
from unittest.mock import patch
from jose import JWTError
from app.core.security import create_access_token, decode_access_token
from app.core.config import settings


class TestCreateAccessToken:
    """Test cases for create_access_token function."""
    
    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string token."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_includes_user_data(self):
        """Test that token includes the provided user data."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded["id_usuario"] == 1
        assert decoded["rol"] == "user"
    
    def test_create_access_token_includes_expiration(self):
        """Test that token includes expiration time."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)
    
    def test_create_access_token_uses_custom_expiration_delta(self):
        """Test that custom expiration delta is used when provided."""
        data = {"id_usuario": 1, "rol": "user"}
        custom_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=custom_delta)
        decoded = decode_access_token(token)
        
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_exp = now + custom_delta
        
        assert abs((exp_time - expected_exp).total_seconds()) < 5
    
    def test_create_access_token_uses_default_expiration_when_none_provided(self):
        """Test that default expiration from settings is used when no delta provided."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_exp = now + timedelta(minutes=settings.jwt_expiration_minutes)
        
        assert abs((exp_time - expected_exp).total_seconds()) < 5
    
    def test_create_access_token_handles_multiple_data_fields(self):
        """Test that token can handle multiple data fields."""
        data = {"id_usuario": 1, "rol": "user", "extra": "value"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded["id_usuario"] == 1
        assert decoded["rol"] == "user"
        assert decoded["extra"] == "value"
    
    def test_create_access_token_does_not_modify_original_data(self):
        """Test that original data dictionary is not modified."""
        data = {"id_usuario": 1, "rol": "user"}
        original_data = data.copy()
        create_access_token(data)
        
        assert data == original_data
        assert "exp" not in data
    
    def test_create_access_token_uses_correct_algorithm(self):
        """Test that token is created with correct algorithm."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded is not None
    
    def test_create_access_token_uses_correct_secret_key(self):
        """Test that token is created with correct secret key."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["id_usuario"] == 1
    
    def test_create_access_token_expiration_is_future_time(self):
        """Test that token expiration is in the future."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        assert exp_time > now


class TestDecodeAccessToken:
    """Test cases for decode_access_token function."""
    
    def test_decode_access_token_returns_payload_for_valid_token(self):
        """Test that decode_access_token returns payload for valid token."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["id_usuario"] == 1
        assert decoded["rol"] == "user"
    
    def test_decode_access_token_returns_none_for_invalid_token(self):
        """Test that decode_access_token returns None for invalid token."""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)
        
        assert decoded is None
    
    def test_decode_access_token_returns_none_for_empty_token(self):
        """Test that decode_access_token returns None for empty token."""
        decoded = decode_access_token("")
        
        assert decoded is None
    
    def test_decode_access_token_returns_none_for_malformed_token(self):
        """Test that decode_access_token returns None for malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        decoded = decode_access_token(malformed_token)
        
        assert decoded is None
    
    def test_decode_access_token_returns_none_for_expired_token(self):
        """Test that decode_access_token returns None for expired token."""
        data = {"id_usuario": 1, "rol": "user"}
        expired_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expired_delta)
        
        decoded = decode_access_token(token)
        assert decoded is None
    
    def test_decode_access_token_returns_all_original_fields(self):
        """Test that decode_access_token returns all original data fields."""
        data = {"id_usuario": 1, "rol": "user", "extra": "value"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded["id_usuario"] == 1
        assert decoded["rol"] == "user"
        assert decoded["extra"] == "value"
        assert "exp" in decoded
    
    def test_decode_access_token_handles_different_user_ids(self):
        """Test that decode_access_token handles different user IDs."""
        for user_id in [1, 100, 9999]:
            data = {"id_usuario": user_id, "rol": "user"}
            token = create_access_token(data)
            decoded = decode_access_token(token)
            
            assert decoded["id_usuario"] == user_id
    
    def test_decode_access_token_handles_different_roles(self):
        """Test that decode_access_token handles different roles."""
        roles = ["user", "admin", "moderator"]
        for role in roles:
            data = {"id_usuario": 1, "rol": role}
            token = create_access_token(data)
            decoded = decode_access_token(token)
            
            assert decoded["rol"] == role
    
    def test_decode_access_token_with_wrong_secret_returns_none(self):
        """Test that decode_access_token returns None for token with wrong secret."""
        data = {"id_usuario": 1, "rol": "user"}
        token = create_access_token(data)
        
        with patch('app.core.security.settings.jwt_secret_key', 'wrong_secret'):
            decoded = decode_access_token(token)
            assert decoded is None
    
    def test_decode_access_token_with_wrong_algorithm_returns_none(self):
        """Test that decode_access_token returns None for token with wrong algorithm."""
        from jose import jwt
        data = {"id_usuario": 1, "rol": "user", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        wrong_algorithm_token = jwt.encode(data, settings.jwt_secret_key, algorithm="HS512")
        
        decoded = decode_access_token(wrong_algorithm_token)
        assert decoded is None

