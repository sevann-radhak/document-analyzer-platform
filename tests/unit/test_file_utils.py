"""Unit tests for file utilities."""
import pytest
from unittest.mock import Mock
from app.utils.file_utils import (
    get_file_extension,
    get_file_type,
    get_content_type,
    is_image_file,
    is_document_file,
    generate_s3_key,
    resolve_s3_key_collision
)
from app.core.constants import FileConstants


class TestGetFileExtension:
    """Test cases for get_file_extension function."""

    def test_get_file_extension_with_extension(self):
        """Test that extension is extracted correctly."""
        assert get_file_extension("test.pdf") == "pdf"
        assert get_file_extension("document.JPG") == "jpg"
        assert get_file_extension("file.name.png") == "png"

    def test_get_file_extension_without_extension(self):
        """Test that empty string is returned for files without extension."""
        assert get_file_extension("testfile") == ""
        assert get_file_extension("") == ""

    def test_get_file_extension_case_insensitive(self):
        """Test that extension is returned in lowercase."""
        assert get_file_extension("test.PDF") == "pdf"
        assert get_file_extension("file.JPG") == "jpg"
        assert get_file_extension("image.PNG") == "png"


class TestGetFileType:
    """Test cases for get_file_type function."""

    def test_get_file_type_pdf(self):
        """Test that PDF files return correct type."""
        assert get_file_type("test.pdf") == FileConstants.FILE_TYPE_PDF
        assert get_file_type("document.PDF") == FileConstants.FILE_TYPE_PDF

    def test_get_file_type_jpg(self):
        """Test that JPG files return correct type."""
        assert get_file_type("test.jpg") == FileConstants.FILE_TYPE_JPG
        assert get_file_type("image.JPG") == FileConstants.FILE_TYPE_JPG
        assert get_file_type("photo.jpeg") == FileConstants.FILE_TYPE_JPG
        assert get_file_type("picture.JPEG") == FileConstants.FILE_TYPE_JPG

    def test_get_file_type_png(self):
        """Test that PNG files return correct type."""
        assert get_file_type("test.png") == FileConstants.FILE_TYPE_PNG
        assert get_file_type("image.PNG") == FileConstants.FILE_TYPE_PNG

    def test_get_file_type_csv(self):
        """Test that CSV files return correct type."""
        assert get_file_type("test.csv") == FileConstants.FILE_TYPE_CSV
        assert get_file_type("data.CSV") == FileConstants.FILE_TYPE_CSV

    def test_get_file_type_unknown_extension(self):
        """Test that unknown extensions return uppercase extension."""
        assert get_file_type("test.txt") == "TXT"
        assert get_file_type("file.doc") == "DOC"

    def test_get_file_type_no_extension(self):
        """Test that files without extension return empty string."""
        assert get_file_type("testfile") == ""


class TestGetContentType:
    """Test cases for get_content_type function."""

    def test_get_content_type_pdf(self):
        """Test that PDF files return correct MIME type."""
        assert get_content_type("test.pdf") == FileConstants.MIME_TYPE_PDF

    def test_get_content_type_jpg(self):
        """Test that JPG files return correct MIME type."""
        assert get_content_type("test.jpg") == FileConstants.MIME_TYPE_JPEG
        assert get_content_type("image.jpeg") == FileConstants.MIME_TYPE_JPEG

    def test_get_content_type_png(self):
        """Test that PNG files return correct MIME type."""
        assert get_content_type("test.png") == FileConstants.MIME_TYPE_PNG

    def test_get_content_type_csv(self):
        """Test that CSV files return correct MIME type."""
        assert get_content_type("test.csv") == FileConstants.MIME_TYPE_CSV

    def test_get_content_type_unknown(self):
        """Test that unknown files return octet-stream."""
        assert get_content_type("test.txt") == FileConstants.MIME_TYPE_OCTET_STREAM
        assert get_content_type("file.unknown") == FileConstants.MIME_TYPE_OCTET_STREAM

    def test_get_content_type_no_extension(self):
        """Test that files without extension return octet-stream."""
        assert get_content_type("testfile") == FileConstants.MIME_TYPE_OCTET_STREAM


class TestIsImageFile:
    """Test cases for is_image_file function."""

    def test_is_image_file_jpg(self):
        """Test that JPG files are recognized as images."""
        assert is_image_file("test.jpg") is True
        assert is_image_file("image.JPG") is True
        assert is_image_file("photo.jpeg") is True
        assert is_image_file("picture.JPEG") is True

    def test_is_image_file_png(self):
        """Test that PNG files are recognized as images."""
        assert is_image_file("test.png") is True
        assert is_image_file("image.PNG") is True

    def test_is_image_file_pdf(self):
        """Test that PDF files are not recognized as images."""
        assert is_image_file("test.pdf") is False

    def test_is_image_file_other(self):
        """Test that other files are not recognized as images."""
        assert is_image_file("test.txt") is False
        assert is_image_file("file.csv") is False

    def test_is_image_file_no_extension(self):
        """Test that files without extension are not recognized as images."""
        assert is_image_file("testfile") is False


class TestIsDocumentFile:
    """Test cases for is_document_file function."""

    def test_is_document_file_pdf(self):
        """Test that PDF files are recognized as documents."""
        assert is_document_file("test.pdf") is True

    def test_is_document_file_jpg(self):
        """Test that JPG files are recognized as documents."""
        assert is_document_file("test.jpg") is True
        assert is_document_file("image.jpeg") is True

    def test_is_document_file_png(self):
        """Test that PNG files are recognized as documents."""
        assert is_document_file("test.png") is True

    def test_is_document_file_other(self):
        """Test that other files are not recognized as documents."""
        assert is_document_file("test.txt") is False
        assert is_document_file("file.csv") is False

    def test_is_document_file_no_extension(self):
        """Test that files without extension are not recognized as documents."""
        assert is_document_file("testfile") is False


class TestGenerateS3Key:
    """Test cases for generate_s3_key function."""

    def test_generate_s3_key_with_extension(self):
        """Test that S3 key is generated correctly with file extension."""
        key = generate_s3_key("test.pdf", "uploads")
        assert key.startswith("uploads/")
        assert "test" in key
        assert key.endswith(".pdf")
        assert "/" in key

    def test_generate_s3_key_without_extension(self):
        """Test that S3 key is generated correctly without file extension."""
        key = generate_s3_key("testfile", "documents")
        assert key.startswith("documents/")
        assert "testfile" in key

    def test_generate_s3_key_includes_timestamp(self):
        """Test that S3 key includes timestamp by default."""
        key = generate_s3_key("test.pdf", "uploads")
        parts = key.split("_")
        assert len(parts) >= 2

    def test_generate_s3_key_format(self):
        """Test that S3 key follows correct format with timestamp."""
        key = generate_s3_key("invoice.pdf", "documents")
        assert key.startswith("documents/")
        assert "/" in key[9:]
        assert key.endswith(".pdf")

    def test_generate_s3_key_with_uuid(self):
        """Test that S3 key can use UUID instead of timestamp."""
        key = generate_s3_key("test.pdf", "uploads", use_uuid=True)
        assert key.startswith("uploads/")
        assert key.endswith(".pdf")
        assert "/" not in key[8:]  # No date path when using UUID

    def test_generate_s3_key_different_prefixes(self):
        """Test that S3 key uses correct prefix."""
        upload_key = generate_s3_key("test.pdf", "uploads")
        doc_key = generate_s3_key("test.pdf", "documents")
        
        assert upload_key.startswith("uploads/")
        assert doc_key.startswith("documents/")

    def test_generate_s3_key_with_complex_filename(self):
        """Test that S3 key handles complex filenames correctly."""
        key = generate_s3_key("my-document_file-name (1).pdf", "uploads")
        assert key.startswith("uploads/")
        assert key.endswith(".pdf")


class TestResolveS3KeyCollision:
    """Test cases for resolve_s3_key_collision function."""

    def test_resolve_s3_key_collision_no_collision(self):
        """Test that function returns key when no collision exists."""
        exists_checker = Mock(return_value=False)
        key = resolve_s3_key_collision("test.pdf", "uploads", exists_checker)
        
        assert key.startswith("uploads/")
        assert key.endswith(".pdf")
        exists_checker.assert_called_once()

    def test_resolve_s3_key_collision_with_collision(self):
        """Test that function resolves collision by adding counter."""
        call_count = 0
        
        def exists_checker(key):
            nonlocal call_count
            call_count += 1
            return call_count <= 2
        
        key = resolve_s3_key_collision("test.pdf", "uploads", exists_checker)
        
        assert key.startswith("uploads/")
        assert key.endswith(".pdf")
        assert "_" in key
        assert call_count == 3

    def test_resolve_s3_key_collision_max_attempts(self):
        """Test that function raises error after max attempts."""
        exists_checker = Mock(return_value=True)
        
        with pytest.raises(ValueError, match="Unable to generate unique S3 key"):
            resolve_s3_key_collision("test.pdf", "uploads", exists_checker, max_attempts=3)
        
        assert exists_checker.call_count == 4

    def test_resolve_s3_key_collision_without_extension(self):
        """Test that function handles files without extension."""
        exists_checker = Mock(return_value=False)
        key = resolve_s3_key_collision("testfile", "documents", exists_checker)
        
        assert key.startswith("documents/")
        assert "testfile" in key

    def test_resolve_s3_key_collision_multiple_collisions(self):
        """Test that function handles multiple collisions."""
        collision_count = 0
        
        def exists_checker(key):
            nonlocal collision_count
            collision_count += 1
            return collision_count <= 5
        
        key = resolve_s3_key_collision("test.pdf", "uploads", exists_checker)
        
        assert key.startswith("uploads/")
        assert key.endswith(".pdf")
        assert collision_count == 6

