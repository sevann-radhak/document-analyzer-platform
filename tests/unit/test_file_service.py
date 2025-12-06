"""Unit tests for file service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.file_service import upload_csv_file
from app.utils.file_utils import generate_s3_key
from app.schemas.file import FileUploadResponse, ValidationResult, ValidationError
from app.models.file import File
from app.core.constants import ValidationErrorType, FileConstants
from botocore.exceptions import ClientError, BotoCoreError
from tests.unit.conftest import mock_db


@pytest.fixture
def sample_file_record():
    """Create a sample File model instance."""
    file_record = MagicMock(spec=File)
    file_record.id = 1
    file_record.filename = "test.csv"
    file_record.s3_key = "uploads/2025/12/test_1234567890.csv"
    file_record.uploaded_by = 1
    file_record.validation_results = {"is_valid": True, "total_rows": 10}
    file_record.created_at = datetime.now(timezone.utc)
    return file_record


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content."""
    return b"id,name,email\n1,John,john@example.com\n2,Jane,jane@example.com"


@pytest.fixture
def valid_validation_result():
    """Create a valid validation result."""
    return ValidationResult(
        is_valid=True,
        total_rows=2,
        total_errors=0,
        empty_value_errors=[],
        incorrect_type_errors=[],
        duplicate_errors=[]
    )


@pytest.fixture
def invalid_validation_result():
    """Create an invalid validation result with errors."""
    return ValidationResult(
        is_valid=False,
        total_rows=2,
        total_errors=2,
        empty_value_errors=[
            ValidationError(
                row=2,
                column="email",
                error_type=ValidationErrorType.EMPTY,
                message="email field is required",
                value=None
            )
        ],
        incorrect_type_errors=[
            ValidationError(
                row=3,
                column="id",
                error_type=ValidationErrorType.INCORRECT_TYPE,
                message="Expected integer, got string",
                value="abc"
            )
        ],
        duplicate_errors=[]
    )


@pytest.fixture
def mock_file_repository(sample_file_record):
    """Create a mock FileRepository."""
    repo = Mock()
    repo.exists_by_s3_key = Mock(return_value=False)
    repo.create = Mock(return_value=sample_file_record)
    return repo


@pytest.fixture
def mock_s3_client():
    """Create a mock S3Client."""
    client = Mock()
    client.upload_file = Mock(return_value="uploads/2025/12/test_1234567890.csv")
    return client


class TestGenerateS3Key:
    """Test cases for generate_s3_key function."""
    
    def test_generate_s3_key_with_extension(self):
        """Test S3 key generation for file with extension."""
        filename = "test.csv"
        key = generate_s3_key(filename, FileConstants.S3_PREFIX_UPLOADS)
        
        assert key.startswith("uploads/")
        assert filename.split(".")[0] in key
        assert key.endswith(".csv")
        assert "/" in key
    
    def test_generate_s3_key_without_extension(self):
        """Test S3 key generation for file without extension."""
        filename = "testfile"
        key = generate_s3_key(filename, FileConstants.S3_PREFIX_UPLOADS)
        
        assert key.startswith("uploads/")
        assert filename in key
        assert "/" in key
    
    def test_generate_s3_key_includes_timestamp(self):
        """Test that S3 key includes timestamp."""
        filename = "test.csv"
        key = generate_s3_key(filename, FileConstants.S3_PREFIX_UPLOADS)
        
        assert "uploads/" in key
        assert filename.split(".")[0] in key
        parts = key.split("_")
        assert len(parts) >= 2
        timestamp_part = parts[-1].split(".")[0]
        assert timestamp_part.isdigit()
    
    def test_generate_s3_key_format(self):
        """Test that S3 key follows expected format."""
        filename = "data.csv"
        key = generate_s3_key(filename, FileConstants.S3_PREFIX_UPLOADS)
        
        parts = key.split("/")
        assert len(parts) == 4
        assert parts[0] == "uploads"
        assert parts[1].isdigit()
        assert parts[2].isdigit()
        assert parts[3].endswith(".csv")
    
    def test_generate_s3_key_with_complex_filename(self):
        """Test S3 key generation with complex filename."""
        filename = "my-test_file.2024.csv"
        key = generate_s3_key(filename, FileConstants.S3_PREFIX_UPLOADS)
        
        assert "my-test_file" in key
        assert key.endswith(".csv")


class TestUploadCsvFile:
    """Test cases for upload_csv_file function."""
    
    def test_upload_csv_file_success(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        sample_file_record,
        mock_file_repository,
        mock_s3_client
    ):
        """Test successful CSV file upload."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            response = upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1
            )
            
            assert isinstance(response, FileUploadResponse)
            assert response.file_id == sample_file_record.id
            assert response.filename == "test.csv"
            assert response.validation_results.is_valid is True
    
    def test_upload_csv_file_calls_validate_csv(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        mock_file_repository,
        mock_s3_client
    ):
        """Test that validate_csv is called with correct parameters."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv') as mock_validate:
            mock_validate.return_value = valid_validation_result
            
            upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1,
                required_columns=["name"],
                column_types={"id": int},
                unique_columns=["id"]
            )
            
            mock_validate.assert_called_once()
            call_args = mock_validate.call_args
            assert call_args[1]["file_content"] == sample_csv_content
            assert call_args[1]["required_columns"] == ["name"]
            assert call_args[1]["column_types"] == {"id": int}
            assert call_args[1]["unique_columns"] == ["id"]
    
    def test_upload_csv_file_calls_s3_upload(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        mock_file_repository,
        mock_s3_client
    ):
        """Test that S3 upload is called."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1
            )
            
            mock_s3_client.upload_file.assert_called_once()
            call_args = mock_s3_client.upload_file.call_args
            assert call_args[1]["content_type"] == "text/csv"
            assert "s3_key" in call_args[1]
    
    def test_upload_csv_file_calls_repository_create(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        mock_file_repository,
        mock_s3_client
    ):
        """Test that repository create is called."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1
            )
            
            mock_file_repository.create.assert_called_once()
            call_args = mock_file_repository.create.call_args
            assert call_args[1]["filename"] == "test.csv"
            assert call_args[1]["uploaded_by"] == 1
            assert "s3_key" in call_args[1]
            assert "validation_results" in call_args[1]
    
    def test_upload_csv_file_with_additional_parameters(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        mock_file_repository,
        mock_s3_client
    ):
        """Test upload with additional parameters."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            response = upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1,
                param1="value1",
                param2="value2"
            )
            
            assert response.param1 == "value1"
            assert response.param2 == "value2"
    
    def test_upload_csv_file_with_validation_errors(
        self,
        mock_db,
        sample_csv_content,
        invalid_validation_result,
        mock_file_repository,
        mock_s3_client
    ):
        """Test upload with validation errors still processes file."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=invalid_validation_result):
            
            response = upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1
            )
            
            assert response.validation_results.is_valid is False
            assert response.validation_results.total_errors == 2
            assert len(response.validation_results.empty_value_errors) == 1
            assert len(response.validation_results.incorrect_type_errors) == 1
    
    def test_upload_csv_file_handles_duplicate_s3_key(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        sample_file_record,
        mock_s3_client
    ):
        """Test that duplicate S3 keys are handled by regenerating."""
        mock_repo = Mock()
        mock_repo.exists_by_s3_key = Mock(side_effect=[True, False])
        mock_repo.create = Mock(return_value=sample_file_record)
        
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_repo), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1
            )
            
            assert mock_repo.exists_by_s3_key.call_count >= 2
    
    def test_upload_csv_file_handles_s3_error(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        mock_file_repository
    ):
        """Test that S3 errors are properly raised."""
        mock_s3 = Mock()
        mock_s3.upload_file = Mock(side_effect=ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='UploadFile'
        ))
        
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            with pytest.raises(ClientError):
                upload_csv_file(
                    db=mock_db,
                    file_content=sample_csv_content,
                    filename="test.csv",
                    uploaded_by=1
                )
    
    def test_upload_csv_file_handles_boto_error(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        mock_file_repository
    ):
        """Test that BotoCore errors are properly raised."""
        mock_s3 = Mock()
        mock_s3.upload_file = Mock(side_effect=BotoCoreError())
        
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            with pytest.raises(BotoCoreError):
                upload_csv_file(
                    db=mock_db,
                    file_content=sample_csv_content,
                    filename="test.csv",
                    uploaded_by=1
                )
    
    def test_upload_csv_file_saves_validation_results(
        self,
        mock_db,
        sample_csv_content,
        invalid_validation_result,
        mock_file_repository,
        mock_s3_client
    ):
        """Test that validation results are saved to database."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=invalid_validation_result):
            
            upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1
            )
            
            call_args = mock_file_repository.create.call_args
            validation_results = call_args[1]["validation_results"]
            assert validation_results["is_valid"] is False
            assert validation_results["total_errors"] == 2
    
    def test_upload_csv_file_returns_correct_response_structure(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        sample_file_record,
        mock_file_repository,
        mock_s3_client
    ):
        """Test that response has all required fields."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            response = upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1
            )
            
            assert hasattr(response, "file_id")
            assert hasattr(response, "filename")
            assert hasattr(response, "s3_key")
            assert hasattr(response, "uploaded_at")
            assert hasattr(response, "validation_results")
            assert isinstance(response.validation_results, ValidationResult)
    
    def test_upload_csv_file_with_empty_optional_parameters(
        self,
        mock_db,
        sample_csv_content,
        valid_validation_result,
        mock_file_repository,
        mock_s3_client
    ):
        """Test upload with None optional parameters."""
        with patch('app.services.file_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.file_service.FileRepository', return_value=mock_file_repository), \
             patch('app.services.file_service.validate_csv', return_value=valid_validation_result):
            
            response = upload_csv_file(
                db=mock_db,
                file_content=sample_csv_content,
                filename="test.csv",
                uploaded_by=1,
                param1=None,
                param2=None,
                required_columns=None,
                column_types=None,
                unique_columns=None
            )
            
            assert response.param1 is None
            assert response.param2 is None

