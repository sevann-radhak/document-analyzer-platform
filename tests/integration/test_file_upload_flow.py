"""Integration tests for file upload flow."""
import pytest
import io
from fastapi import status
from unittest.mock import patch, MagicMock


class TestFileUploadFlow:
    """Test cases for file upload endpoint."""
    
    def test_upload_file_requires_authentication(self, client):
        """Test that file upload requires authentication."""
        csv_content = b"id,name,email\n1,John,john@example.com"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        
        response = client.post("/api/v1/files/upload", files=files)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @patch('app.utils.aws_client.get_s3_client')
    def test_upload_file_with_valid_csv(self, mock_s3, client, auth_headers):
        """Test uploading a valid CSV file."""
        mock_s3_client = mock_s3.return_value
        mock_s3_client.upload_file = MagicMock()
        
        csv_content = b"id,name,email\n1,John Doe,john@example.com\n2,Jane Smith,jane@example.com"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        
        response = client.post(
            "/api/v1/files/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "file_id" in data
        assert "filename" in data
        assert "s3_key" in data
        assert "validation_results" in data
        assert data["filename"] == "test.csv"
    
    @patch('app.utils.aws_client.get_s3_client')
    def test_upload_file_rejects_non_csv(self, mock_s3, client, auth_headers):
        """Test that non-CSV files are rejected."""
        mock_s3_client = mock_s3.return_value
        
        file_content = b"This is not a CSV file"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post(
            "/api/v1/files/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "CSV" in response.json()["detail"]
    
    @patch('app.utils.aws_client.get_s3_client')
    def test_upload_file_rejects_empty_file(self, mock_s3, client, auth_headers):
        """Test that empty files are rejected."""
        mock_s3_client = mock_s3.return_value
        
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        
        response = client.post(
            "/api/v1/files/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "empty" in response.json()["detail"].lower()
    
    @patch('app.utils.aws_client.get_s3_client')
    def test_upload_file_with_additional_parameters(self, mock_s3, client, auth_headers):
        """Test uploading file with additional parameters."""
        mock_s3_client = mock_s3.return_value
        mock_s3_client.upload_file = MagicMock()
        
        csv_content = b"id,name\n1,Test"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        data = {"param1": "value1", "param2": "value2"}
        
        response = client.post(
            "/api/v1/files/upload",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data.get("param1") == "value1"
        assert response_data.get("param2") == "value2"


class TestCompleteFileUploadFlow:
    """Test complete flow: login -> upload."""
    
    @patch('app.utils.aws_client.get_s3_client')
    def test_complete_flow_login_then_upload(self, mock_s3, client, test_db):
        """Test complete flow: login then upload file."""
        mock_s3_client = mock_s3.return_value
        mock_s3_client.upload_file = MagicMock()
        
        login_response = client.post("/api/v1/auth/login", json={})
        assert login_response.status_code == status.HTTP_200_OK
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        csv_content = b"id,name,email\n1,John,john@example.com"
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        
        upload_response = client.post(
            "/api/v1/files/upload",
            files=files,
            headers=headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        
        from app.models.file import File
        file_count = test_db.query(File).count()
        assert file_count >= 1

