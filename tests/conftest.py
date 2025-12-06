import warnings
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.utils.database import Base, get_db
from app.core.config import settings

# Suppress openpyxl deprecation warnings
# These warnings come from openpyxl library using deprecated datetime.utcnow()
warnings.filterwarnings("ignore", message=".*datetime.datetime.utcnow.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="openpyxl")


@pytest.fixture
def client() -> TestClient:
    """Create a test client for API testing."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Create a test database session."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

