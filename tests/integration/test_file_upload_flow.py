"""Integration tests for file upload flow."""
import io
from fastapi import status


class TestFileUploadFlow:
    """Test cases for file upload endpoint."""
    
    def test_upload_file_requires_authentication(self, client):
        """Test that file upload requires authentication."""
        csv_content = b"id,name,email\n1,John,john@example.com"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        
        response = client.post("/api/v1/files/upload", files=files)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
