"""Integration tests for events flow."""
import pytest
import io
from fastapi import status
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.ai_service import DocumentClassification


class TestEventsListFlow:
    """Test cases for events list endpoint."""
    
    def test_get_events_requires_authentication(self, client):
        """Test that getting events requires authentication."""
        response = client.get("/api/v1/events")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_events_with_authentication(self, client, auth_headers, test_db):
        """Test getting events with authentication."""
        from app.services.event_service import create_event
        
        create_event(
            db=test_db,
            event_type="Document upload",
            description="Test event",
            user_id=1
        )
        test_db.commit()
        
        response = client.get("/api/v1/events", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "events" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["events"], list)
        assert data["total"] >= 1
    
    def test_get_events_with_filters(self, client, auth_headers, test_db):
        """Test getting events with filters."""
        from app.services.event_service import create_event
        
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
            headers=auth_headers
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
    
    def test_export_events_with_authentication(self, client, auth_headers, test_db):
        """Test exporting events with authentication."""
        from app.services.event_service import create_event
        
        create_event(
            db=test_db,
            event_type="Document upload",
            description="Test event",
            user_id=1
        )
        test_db.commit()
        
        response = client.get("/api/v1/events/export", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["content-disposition"]
        assert response.content is not None
        assert len(response.content) > 0
    
    def test_export_events_no_events_found(self, client, auth_headers, test_db):
        """Test exporting events when no events match filters."""
        response = client.get(
            "/api/v1/events/export?event_type=Nonexistent",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCompleteEventsFlow:
    """Test complete flow: login -> upload -> events."""
    
    @patch('app.services.document_service.OpenAIService')
    @patch('app.utils.aws_client.get_s3_client')
    def test_complete_flow_with_events(self, mock_s3, mock_openai, client, test_db):
        """Test complete flow: login, upload, check events."""
        mock_s3_client = mock_s3.return_value
        mock_s3_client.upload_file = MagicMock()
        
        mock_ai_instance = mock_openai.return_value
        mock_ai_instance.analyze_document = AsyncMock(return_value={
            "classification": DocumentClassification.INVOICE,
            "extracted_data": {
                "client": {"name": "Client", "address": "Address"},
                "provider": {"name": "Provider", "address": "Address"},
                "invoice_number": "INV-001",
                "date": "2024-12-06",
                "products": [],
                "invoice_total": 0.0
            }
        })
        
        login_response = client.post("/api/v1/auth/login", json={})
        assert login_response.status_code == status.HTTP_200_OK
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        file_content = b"fake invoice content"
        files = {"file": ("invoice.jpg", io.BytesIO(file_content), "image/jpeg")}
        
        upload_response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=headers
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        
        events_response = client.get("/api/v1/events", headers=headers)
        assert events_response.status_code == status.HTTP_200_OK
        
        events_data = events_response.json()
        assert events_data["total"] >= 1
        
        export_response = client.get("/api/v1/events/export", headers=headers)
        assert export_response.status_code == status.HTTP_200_OK

