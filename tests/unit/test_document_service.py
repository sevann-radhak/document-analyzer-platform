"""Unit tests for document service."""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from botocore.exceptions import ClientError, BotoCoreError

from app.services.document_service import upload_and_analyze_document
from app.utils.file_utils import (
    generate_s3_key,
    get_file_type,
    get_content_type
)
from app.services.ai_service import DocumentClassification
from app.schemas.document import DocumentResponse, InvoiceData, InformationData
from app.models.document import Document
from app.core.constants import ErrorMessages, FileConstants
from tests.unit.conftest import mock_db


@pytest.fixture
def sample_document_record():
    """Create a sample Document model instance."""
    document = Document(
        id=1,
        filename="test_invoice.pdf",
        file_type="PDF",
        s3_key="documents/2025/12/test_invoice_1234567890.pdf",
        classification="Invoice",
        extracted_data={
            "client": {"name": "Test Client", "address": "123 Test St"},
            "provider": {"name": "Test Provider", "address": "456 Provider Ave"},
            "invoice_number": "INV-001",
            "date": "2025-12-06",
            "products": [],
            "invoice_total": 100.0
        }
    )
    document.created_at = datetime.now(timezone.utc)
    return document


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    ai_service = Mock()
    ai_service.analyze_document = AsyncMock(return_value={
        "classification": DocumentClassification.INVOICE,
        "extracted_data": {
            "client": {"name": "Test Client", "address": "123 Test St"},
            "provider": {"name": "Test Provider", "address": "456 Provider Ave"},
            "invoice_number": "INV-001",
            "date": "2025-12-06",
            "products": [],
            "invoice_total": 100.0
        }
    })
    return ai_service


@pytest.fixture
def mock_ai_service_information():
    """Create a mock AI service for Information documents."""
    ai_service = Mock()
    ai_service.analyze_document = AsyncMock(return_value={
        "classification": DocumentClassification.INFORMATION,
        "extracted_data": {
            "description": "Test document",
            "content_summary": "This is a test document summary",
            "sentiment": "positive"
        }
    })
    return ai_service


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    s3_client = Mock()
    s3_client.upload_file = Mock()
    return s3_client


@pytest.fixture
def mock_document_repository(sample_document_record):
    """Create a mock DocumentRepository."""
    repo = Mock()
    repo.exists_by_s3_key = Mock(return_value=False)
    repo.create = Mock(return_value=sample_document_record)
    return repo


class TestGenerateDocumentS3Key:
    """Test cases for generate_s3_key function for documents."""

    def test_generate_document_s3_key_with_extension(self):
        """Test that S3 key is generated correctly with file extension."""
        filename = "test.pdf"
        s3_key = generate_s3_key(filename, FileConstants.S3_PREFIX_DOCUMENTS)
        
        assert s3_key.startswith("documents/")
        assert "test" in s3_key
        assert s3_key.endswith(".pdf")
        assert "/" in s3_key

    def test_generate_document_s3_key_without_extension(self):
        """Test that S3 key is generated correctly without file extension."""
        filename = "testfile"
        s3_key = generate_s3_key(filename, FileConstants.S3_PREFIX_DOCUMENTS)
        
        assert s3_key.startswith("documents/")
        assert "testfile" in s3_key

    def test_generate_document_s3_key_includes_timestamp(self):
        """Test that S3 key includes timestamp."""
        filename = "test.pdf"
        s3_key = generate_s3_key(filename, FileConstants.S3_PREFIX_DOCUMENTS)
        
        parts = s3_key.split("_")
        assert len(parts) >= 2

    def test_generate_document_s3_key_format(self):
        """Test that S3 key follows correct format."""
        filename = "invoice.pdf"
        s3_key = generate_s3_key(filename, FileConstants.S3_PREFIX_DOCUMENTS)
        
        assert s3_key.startswith("documents/")
        assert "/" in s3_key[10:]
        assert s3_key.endswith(".pdf")

    def test_generate_document_s3_key_with_complex_filename(self):
        """Test that S3 key handles complex filenames correctly."""
        filename = "my-document_file-name (1).pdf"
        s3_key = generate_s3_key(filename, FileConstants.S3_PREFIX_DOCUMENTS)
        
        assert s3_key.startswith("documents/")
        assert s3_key.endswith(".pdf")


class TestGetFileType:
    """Test cases for get_file_type function."""

    def test_get_file_type_pdf(self):
        """Test that PDF files return 'PDF'."""
        assert get_file_type("test.pdf") == FileConstants.FILE_TYPE_PDF
        assert get_file_type("document.PDF") == FileConstants.FILE_TYPE_PDF

    def test_get_file_type_jpg(self):
        """Test that JPG files return 'JPG'."""
        assert get_file_type("test.jpg") == FileConstants.FILE_TYPE_JPG
        assert get_file_type("image.JPG") == FileConstants.FILE_TYPE_JPG
        assert get_file_type("photo.jpeg") == FileConstants.FILE_TYPE_JPG
        assert get_file_type("picture.JPEG") == FileConstants.FILE_TYPE_JPG

    def test_get_file_type_png(self):
        """Test that PNG files return 'PNG'."""
        assert get_file_type("test.png") == FileConstants.FILE_TYPE_PNG
        assert get_file_type("image.PNG") == FileConstants.FILE_TYPE_PNG

    def test_get_file_type_unknown_extension(self):
        """Test that unknown extensions return uppercase extension."""
        assert get_file_type("test.txt") == "TXT"
        assert get_file_type("file.doc") == "DOC"


class TestGetContentType:
    """Test cases for get_content_type function."""

    def test_get_content_type_pdf(self):
        """Test that PDF files return correct content type."""
        assert get_content_type("test.pdf") == FileConstants.MIME_TYPE_PDF

    def test_get_content_type_jpg(self):
        """Test that JPG files return correct content type."""
        assert get_content_type("test.jpg") == FileConstants.MIME_TYPE_JPEG
        assert get_content_type("image.jpeg") == FileConstants.MIME_TYPE_JPEG

    def test_get_content_type_png(self):
        """Test that PNG files return correct content type."""
        assert get_content_type("test.png") == FileConstants.MIME_TYPE_PNG

    def test_get_content_type_unknown(self):
        """Test that unknown extensions return default content type."""
        assert get_content_type("test.txt") == FileConstants.MIME_TYPE_OCTET_STREAM


class TestUploadAndAnalyzeDocument:
    """Test cases for upload_and_analyze_document function."""

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_success_invoice(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository,
        sample_document_record
    ):
        """Test successful document upload and analysis for Invoice."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            file_content = b"fake pdf content"
            filename = "invoice.pdf"
            
            result = await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service,
                user_id=1
            )
            
            assert isinstance(result, DocumentResponse)
            assert result.document_id == 1
            assert result.filename == "test_invoice.pdf"
            assert result.classification == DocumentClassification.INVOICE
            assert isinstance(result.extracted_data, InvoiceData)

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_success_information(
        self,
        mock_db,
        mock_ai_service_information,
        mock_s3_client,
        mock_document_repository
    ):
        """Test successful document upload and analysis for Information."""
        document_info = Document(
            id=2,
            filename="info.pdf",
            file_type="PDF",
            s3_key="documents/2025/12/info_1234567890.pdf",
            classification="Information",
            extracted_data={
                "description": "Test document",
                "content_summary": "This is a test document summary",
                "sentiment": "positive"
            }
        )
        document_info.created_at = datetime.now(timezone.utc)
        
        mock_document_repository.create = Mock(return_value=document_info)
        
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            file_content = b"fake pdf content"
            filename = "info.pdf"
            
            result = await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service_information,
                user_id=1
            )
            
            assert isinstance(result, DocumentResponse)
            assert result.classification == DocumentClassification.INFORMATION
            assert isinstance(result.extracted_data, InformationData)

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_calls_s3_upload(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that S3 upload is called with correct parameters."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service
            )
            
            mock_s3_client.upload_file.assert_called_once()
            call_args = mock_s3_client.upload_file.call_args
            assert call_args[1]["content_type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_calls_ai_service(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that AI service analyze_document is called."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service
            )
            
            mock_ai_service.analyze_document.assert_called_once_with(
                file_content=file_content,
                filename=filename
            )

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_calls_repository_create(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that document repository create is called."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service
            )
            
            mock_document_repository.create.assert_called_once()
            call_args = mock_document_repository.create.call_args
            assert call_args[1]["filename"] == "test.pdf"
            assert call_args[1]["file_type"] == "PDF"
            assert call_args[1]["classification"] == "Invoice"

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_raises_error_for_invalid_file_type(
        self,
        mock_db,
        mock_ai_service
    ):
        """Test that ValueError is raised for invalid file types."""
        file_content = b"fake content"
        filename = "test.txt"
        
        with pytest.raises(ValueError) as exc_info:
            await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service
            )
        
        assert ErrorMessages.AI_UNSUPPORTED_FILE_TYPE.format(file_type="TXT") in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_handles_s3_error(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that S3 errors are handled correctly."""
        mock_s3_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "PutObject"
        )
        
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            with pytest.raises(ValueError) as exc_info:
                await upload_and_analyze_document(
                    db=mock_db,
                    file_content=file_content,
                    filename=filename,
                    ai_service=mock_ai_service
                )
            
            assert ErrorMessages.S3_UPLOAD_ERROR.format(error="") in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_handles_ai_error(
        self,
        mock_db,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that AI service errors are handled correctly."""
        mock_ai_service = Mock()
        mock_ai_service.analyze_document = AsyncMock(side_effect=ValueError("AI processing failed"))
        
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            with pytest.raises(ValueError) as exc_info:
                await upload_and_analyze_document(
                    db=mock_db,
                    file_content=file_content,
                    filename=filename,
                    ai_service=mock_ai_service
                )
            
            assert ErrorMessages.AI_DOCUMENT_PROCESSING_ERROR.format(error="") in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_handles_duplicate_s3_key(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that duplicate S3 keys are handled by generating new keys."""
        mock_document_repository.exists_by_s3_key = Mock(side_effect=[True, False])
        
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            result = await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service
            )
            
            assert mock_document_repository.exists_by_s3_key.call_count >= 2
            assert isinstance(result, DocumentResponse)

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_logs_events(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that event logging functions are called."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification') as mock_log_ai, \
             patch('app.services.document_service.log_document_upload') as mock_log_upload:
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service,
                user_id=1
            )
            
            mock_log_ai.assert_called_once()
            mock_log_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_handles_logging_errors(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that logging errors don't interrupt the main flow."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification', side_effect=Exception("Logging error")), \
             patch('app.services.document_service.log_document_upload', side_effect=Exception("Logging error")):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            result = await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service
            )
            
            assert isinstance(result, DocumentResponse)

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_creates_openai_service_when_none_provided(
        self,
        mock_db,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that OpenAIService is created when ai_service is None."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.OpenAIService') as mock_openai_class, \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            mock_ai_instance = Mock()
            mock_ai_instance.analyze_document = AsyncMock(return_value={
                "classification": DocumentClassification.INVOICE,
                "extracted_data": {
                    "client": {"name": "Test", "address": "123"},
                    "provider": {"name": "Test", "address": "456"},
                    "invoice_number": "INV-001",
                    "date": "2025-12-06",
                    "products": [],
                    "invoice_total": 100.0
                }
            })
            mock_openai_class.return_value = mock_ai_instance
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=None
            )
            
            mock_openai_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_and_analyze_document_returns_correct_response_structure(
        self,
        mock_db,
        mock_ai_service,
        mock_s3_client,
        mock_document_repository
    ):
        """Test that the response has all required fields."""
        with patch('app.services.document_service.get_s3_client', return_value=mock_s3_client), \
             patch('app.services.document_service.DocumentRepository', return_value=mock_document_repository), \
             patch('app.services.document_service.log_ai_classification'), \
             patch('app.services.document_service.log_document_upload'):
            
            file_content = b"fake pdf content"
            filename = "test.pdf"
            
            result = await upload_and_analyze_document(
                db=mock_db,
                file_content=file_content,
                filename=filename,
                ai_service=mock_ai_service
            )
            
            assert hasattr(result, 'document_id')
            assert hasattr(result, 'filename')
            assert hasattr(result, 'file_type')
            assert hasattr(result, 's3_key')
            assert hasattr(result, 'classification')
            assert hasattr(result, 'extracted_data')
            assert hasattr(result, 'uploaded_at')

