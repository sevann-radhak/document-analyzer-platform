"""Shared fixtures for integration tests."""
import warnings
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.utils.database import Base, get_db
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
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    return create_access_token({"id_usuario": 1, "rol": UserRoles.USER})
