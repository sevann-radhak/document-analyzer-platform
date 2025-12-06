"""Integration tests for events flow."""
import pytest
from fastapi import status
from app.core.security import create_access_token
from app.core.constants import UserRoles


class TestEventsListFlow:
    """Test cases for events list endpoint."""
    
    def test_get_events_requires_authentication(self, client):
        """Test that getting events requires authentication."""
        response = client.get("/api/v1/events")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_events_with_authentication(self, client, test_db, valid_jwt_token):
        """Test getting events with authentication."""
        from app.services.event_service import create_event
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        create_event(
            db=test_db,
            event_type="Document upload",
            description="Test event",
            user_id=1
        )
        test_db.commit()
        test_db.flush()
        
        response = client.get("/api/v1/events", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "events" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["events"], list)
        assert data["total"] >= 0
    
    def test_get_events_with_filters(self, client, test_db, valid_jwt_token):
        """Test getting events with filters."""
        from app.services.event_service import create_event
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        create_event(
            db=test_db,
            event_type="Document upload",
            description="Invoice document",
            user_id=1
        )
        create_event(
            db=test_db,
            event_type="AI",
            description="Classification",
            user_id=1
        )
        test_db.commit()
        
        response = client.get(
            "/api/v1/events?event_type=Document%20upload",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert all(event["event_type"] == "Document upload" for event in data["events"])


class TestEventsExportFlow:
    """Test cases for events export endpoint."""
    
    def test_export_events_requires_authentication(self, client):
        """Test that exporting events requires authentication."""
        response = client.get("/api/v1/events/export")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
