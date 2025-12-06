"""Shared fixtures for unit tests."""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.constants import UserRoles


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock(spec=Session)
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(id=1, rol=UserRoles.USER)


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    return User(id=2, rol=UserRoles.ADMIN)


@pytest.fixture
def mock_create_anonymous_user(sample_user):
    """Mock for create_anonymous_user function."""
    with patch('app.services.auth_service.create_anonymous_user', return_value=sample_user) as mock:
        yield mock


@pytest.fixture
def mock_create_access_token():
    """Mock for create_access_token function."""
    with patch('app.services.auth_service.create_access_token', return_value="test_token") as mock:
        yield mock

