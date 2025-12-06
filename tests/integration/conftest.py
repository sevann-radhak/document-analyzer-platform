"""Shared fixtures for integration tests."""
import warnings
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from typing import Generator

from app.main import app
from app.utils.database import Base, get_db
from app.models.user import User
from app.core.constants import UserRoles
from app.core.security import create_access_token

# Suppress openpyxl deprecation warnings
# These warnings come from openpyxl library using deprecated datetime.utcnow()
warnings.filterwarnings("ignore", message=".*datetime.datetime.utcnow.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="openpyxl")


@pytest.fixture(scope="function")
def test_db():
    """Create a test database in memory."""
    import app.models.user
    import app.models.file
    import app.models.event
    import app.models.document
    
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db) -> TestClient:
    """Create a test client with test database override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for file operations."""
    with patch('app.utils.aws_client.get_s3_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.upload_file = MagicMock()
        mock_client.download_file = MagicMock()
        mock_client.delete_file = MagicMock()
        mock_client.file_exists = MagicMock(return_value=False)
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service for document analysis."""
    with patch('app.services.document_service.OpenAIService') as mock_class:
        mock_instance = MagicMock()
        mock_instance.analyze_document = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def auth_token(client, test_db):
    """Get authentication token by performing login."""
    with patch('app.services.auth_service.create_anonymous_user') as mock_create_user:
        from app.models.user import User
        mock_user = User(id=1, rol=UserRoles.USER)
        test_db.add(mock_user)
        test_db.commit()
        mock_create_user.return_value = mock_user
        
        response = client.post("/api/v1/auth/login", json={})
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            token = create_access_token({"id_usuario": 1, "rol": UserRoles.USER})
            return token


@pytest.fixture
def auth_headers(auth_token):
    """Get authentication headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    return create_access_token({"id_usuario": 1, "rol": UserRoles.USER})


@pytest.fixture
def auth_headers_with_valid_token(valid_jwt_token):
    """Get authentication headers with a valid JWT token."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}
