"""Integration tests for document analysis flow."""
import pytest
import io
from fastapi import status
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.ai_service import DocumentClassification, SentimentType


class TestDocumentUploadFlow:
    """Test cases for document upload and analysis endpoint."""
    
    def test_upload_document_requires_authentication(self, client):
        """Test that document upload requires authentication."""
        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @patch('app.services.document_service.OpenAIService')
    @patch('app.utils.aws_client.get_s3_client')
    def test_upload_document_invoice(self, mock_s3, mock_openai, client, auth_headers):
        """Test uploading and analyzing an invoice document."""
        mock_s3_client = mock_s3.return_value
        mock_s3_client.upload_file = MagicMock()
        
        mock_ai_instance = mock_openai.return_value
        mock_ai_instance.analyze_document = AsyncMock(return_value={
            "classification": DocumentClassification.INVOICE,
            "extracted_data": {
                "client": {"name": "Test Client", "address": "123 Test St"},
                "provider": {"name": "Test Provider", "address": "456 Provider Ave"},
                "invoice_number": "INV-001",
                "date": "2024-12-06",
                "products": [
                    {"quantity": 1, "name": "Item A", "unit_price": 10.0, "total": 10.0}
                ],
                "invoice_total": 10.0
            }
        })
        
        file_content = b"fake invoice image content"
        files = {"file": ("invoice.jpg", io.BytesIO(file_content), "image/jpeg")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "document_id" in data
        assert "filename" in data
        assert "classification" in data
        assert "extracted_data" in data
        assert data["classification"] == "Invoice"
        assert "invoice_number" in data["extracted_data"]
    
    @patch('app.services.document_service.OpenAIService')
    @patch('app.utils.aws_client.get_s3_client')
    def test_upload_document_information(self, mock_s3, mock_openai, client, auth_headers):
        """Test uploading and analyzing an information document."""
        mock_s3_client = mock_s3.return_value
        mock_s3_client.upload_file = MagicMock()
        
        mock_ai_instance = mock_openai.return_value
        mock_ai_instance.analyze_document = AsyncMock(return_value={
            "classification": DocumentClassification.INFORMATION,
            "extracted_data": {
                "description": "Test document",
                "content_summary": "This is a test summary",
                "sentiment": SentimentType.NEUTRAL.value
            }
        })
        
        file_content = b"fake information image content"
        files = {"file": ("report.png", io.BytesIO(file_content), "image/png")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["classification"] == "Information"
        assert "description" in data["extracted_data"]
        assert "content_summary" in data["extracted_data"]
        assert "sentiment" in data["extracted_data"]
    
    def test_upload_document_rejects_invalid_file_type(self, client, auth_headers):
        """Test that invalid file types are rejected."""
        file_content = b"invalid file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCompleteDocumentAnalysisFlow:
    """Test complete flow: login -> upload -> analysis."""
    
    @patch('app.services.document_service.OpenAIService')
    @patch('app.utils.aws_client.get_s3_client')
    def test_complete_flow_login_upload_analyze(self, mock_s3, mock_openai, client, test_db):
        """Test complete flow: login, upload document, analyze."""
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
        
        from app.models.document import Document
        document_count = test_db.query(Document).count()
        assert document_count >= 1
        
        from app.models.event import Event
        event_count = test_db.query(Event).count()
        assert event_count >= 1

