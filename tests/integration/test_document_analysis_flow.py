"""Integration tests for document analysis flow."""
import io
from fastapi import status


class TestDocumentUploadFlow:
    """Test cases for document upload and analysis endpoint."""
    
    def test_upload_document_requires_authentication(self, client):
        """Test that document upload requires authentication."""
        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_upload_document_rejects_invalid_file_type(self, client, valid_jwt_token):
        """Test that invalid file types are rejected."""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        file_content = b"invalid file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
