"""Unit tests for token renewal functionality."""
import pytest
from datetime import timedelta, datetime, timezone
from unittest.mock import patch, Mock
from app.services.auth_service import refresh_token
from app.core.security import create_access_token, decode_access_token
from app.core.config import settings
from app.core.constants import UserRoles, TokenType, ErrorMessages


class TestRefreshToken:
    """Test cases for refresh_token function."""

    def test_refresh_token_returns_new_token_for_valid_token(self):
        """Test that refresh_token returns a new token for a valid token."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        
        assert "access_token" in result
        assert isinstance(result["access_token"], str)
        assert len(result["access_token"]) > 0

    def test_refresh_token_returns_valid_new_token(self):
        """Test that refresh_token returns a valid new token that can be decoded."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        new_token = result["access_token"]
        new_decoded = decode_access_token(new_token)
        
        assert new_decoded is not None
        assert new_decoded["id_usuario"] == 1
        assert new_decoded["rol"] == UserRoles.USER
        assert "exp" in new_decoded
        assert new_decoded["exp"] >= int(datetime.now(timezone.utc).timestamp())

    def test_refresh_token_preserves_user_id(self):
        """Test that the new token preserves the user ID from the original token."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        new_token = result["access_token"]
        decoded = decode_access_token(new_token)
        
        assert decoded is not None
        assert decoded["id_usuario"] == 1

    def test_refresh_token_preserves_user_role(self):
        """Test that the new token preserves the user role from the original token."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        new_token = result["access_token"]
        decoded = decode_access_token(new_token)
        
        assert decoded is not None
        assert decoded["rol"] == UserRoles.USER

    def test_refresh_token_returns_correct_token_type(self):
        """Test that refresh_token returns correct token type."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        
        assert result["token_type"] == TokenType.BEARER

    def test_refresh_token_returns_correct_expires_in(self):
        """Test that refresh_token returns correct expiration time."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        
        assert result["expires_in"] == settings.jwt_expiration_minutes

    def test_refresh_token_returns_complete_response_structure(self):
        """Test that refresh_token returns all required fields."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        
        required_fields = ["access_token", "token_type", "expires_in"]
        for field in required_fields:
            assert field in result

    def test_refresh_token_handles_different_user_ids(self):
        """Test that refresh_token handles different user IDs."""
        for user_id in [1, 100, 9999]:
            data = {"id_usuario": user_id, "rol": UserRoles.USER}
            original_token = create_access_token(data)
            
            result = refresh_token(original_token)
            new_token = result["access_token"]
            decoded = decode_access_token(new_token)
            
            assert decoded is not None
            assert decoded["id_usuario"] == user_id

    def test_refresh_token_handles_different_roles(self):
        """Test that refresh_token handles different user roles."""
        roles = [UserRoles.USER, UserRoles.ADMIN, UserRoles.MODERATOR]
        for role in roles:
            data = {"id_usuario": 1, "rol": role}
            original_token = create_access_token(data)
            
            result = refresh_token(original_token)
            new_token = result["access_token"]
            decoded = decode_access_token(new_token)
            
            assert decoded is not None
            assert decoded["rol"] == role

    def test_refresh_token_raises_value_error_for_invalid_token(self):
        """Test that refresh_token raises ValueError for invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(ValueError) as exc_info:
            refresh_token(invalid_token)
        
        assert ErrorMessages.TOKEN_INVALID in str(exc_info.value)

    def test_refresh_token_raises_value_error_for_empty_token(self):
        """Test that refresh_token raises ValueError for empty token."""
        with pytest.raises(ValueError) as exc_info:
            refresh_token("")
        
        assert ErrorMessages.TOKEN_INVALID in str(exc_info.value)

    def test_refresh_token_raises_value_error_for_malformed_token(self):
        """Test that refresh_token raises ValueError for malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        
        with pytest.raises(ValueError) as exc_info:
            refresh_token(malformed_token)
        
        assert ErrorMessages.TOKEN_INVALID in str(exc_info.value)

    def test_refresh_token_raises_value_error_for_expired_token(self):
        """Test that refresh_token raises ValueError for expired token."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        expired_delta = timedelta(seconds=-1)
        expired_token = create_access_token(data, expires_delta=expired_delta)
        
        with pytest.raises(ValueError) as exc_info:
            refresh_token(expired_token)
        
        assert ErrorMessages.TOKEN_INVALID in str(exc_info.value)

    def test_refresh_token_raises_value_error_when_id_usuario_missing(self):
        """Test that refresh_token raises ValueError when id_usuario is missing from payload."""
        payload_without_id = {"rol": UserRoles.USER}
        
        with patch('app.services.auth_service.decode_access_token', return_value=payload_without_id):
            with pytest.raises(ValueError) as exc_info:
                refresh_token("dummy_token")
            
            assert ErrorMessages.TOKEN_INVALID in str(exc_info.value)

    def test_refresh_token_raises_value_error_when_rol_missing(self):
        """Test that refresh_token raises ValueError when rol is missing from payload."""
        payload_without_rol = {"id_usuario": 1}
        
        with patch('app.services.auth_service.decode_access_token', return_value=payload_without_rol):
            with pytest.raises(ValueError) as exc_info:
                refresh_token("dummy_token")
            
            assert ErrorMessages.TOKEN_INVALID in str(exc_info.value)

    def test_refresh_token_raises_value_error_when_payload_is_none(self):
        """Test that refresh_token raises ValueError when decode returns None."""
        with patch('app.services.auth_service.decode_access_token', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                refresh_token("dummy_token")
            
            assert ErrorMessages.TOKEN_INVALID in str(exc_info.value)

    def test_refresh_token_creates_new_token_with_extended_expiration(self):
        """Test that the new token has extended expiration time."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        new_token = result["access_token"]
        decoded = decode_access_token(new_token)
        
        assert decoded is not None
        assert "exp" in decoded
        
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        expected_exp = now + timedelta(minutes=settings.jwt_expiration_minutes)
        
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_refresh_token_can_be_called_multiple_times(self):
        """Test that refresh_token can be called multiple times with the same token."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result1 = refresh_token(original_token)
        result2 = refresh_token(original_token)
        
        decoded1 = decode_access_token(result1["access_token"])
        decoded2 = decode_access_token(result2["access_token"])
        
        assert decoded1 is not None
        assert decoded2 is not None
        assert decoded1["id_usuario"] == decoded2["id_usuario"]
        assert decoded1["rol"] == decoded2["rol"]
        assert result1["token_type"] == result2["token_type"]
        assert result1["expires_in"] == result2["expires_in"]

    def test_refresh_token_only_preserves_id_and_rol(self):
        """Test that refresh_token only preserves id_usuario and rol, not additional fields."""
        data = {"id_usuario": 1, "rol": UserRoles.USER, "extra": "value"}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        new_token = result["access_token"]
        decoded = decode_access_token(new_token)
        
        assert decoded is not None
        assert decoded["id_usuario"] == 1
        assert decoded["rol"] == UserRoles.USER
        assert "extra" not in decoded

    def test_refresh_token_new_token_is_valid(self):
        """Test that the new token returned by refresh_token is valid and can be decoded."""
        data = {"id_usuario": 1, "rol": UserRoles.USER}
        original_token = create_access_token(data)
        
        result = refresh_token(original_token)
        new_token = result["access_token"]
        decoded = decode_access_token(new_token)
        
        assert decoded is not None
        assert decoded["id_usuario"] == 1
        assert decoded["rol"] == UserRoles.USER
        assert "exp" in decoded

