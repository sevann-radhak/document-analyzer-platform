"""Unit tests for AWS S3 client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError
from app.utils.aws_client import S3Client, get_s3_client
from app.core.config import settings
from app.core.constants import ErrorMessages


class TestS3ClientInit:
    """Test cases for S3Client initialization."""
    
    def test_init_with_default_settings(self):
        """Test S3Client initialization with default settings."""
        with patch('app.utils.aws_client.settings') as mock_settings:
            mock_settings.aws_access_key_id = "test_key"
            mock_settings.aws_secret_access_key = "test_secret"
            mock_settings.aws_s3_bucket_name = "test_bucket"
            mock_settings.aws_region = "us-east-1"
            
            client = S3Client()
            
            assert client.access_key_id == "test_key"
            assert client.secret_access_key == "test_secret"
            assert client.bucket_name == "test_bucket"
            assert client.region == "us-east-1"
    
    def test_init_with_custom_credentials(self):
        """Test S3Client initialization with custom credentials."""
        client = S3Client(
            access_key_id="custom_key",
            secret_access_key="custom_secret",
            bucket_name="custom_bucket",
            region="us-west-2"
        )
        
        assert client.access_key_id == "custom_key"
        assert client.secret_access_key == "custom_secret"
        assert client.bucket_name == "custom_bucket"
        assert client.region == "us-west-2"
    
    def test_init_client_is_none_initially(self):
        """Test that client property is None initially."""
        client = S3Client()
        assert client._client is None


class TestS3ClientProperty:
    """Test cases for S3Client client property."""
    
    def test_client_property_creates_client_on_first_access(self):
        """Test that client property creates boto3 client on first access."""
        with patch('app.utils.aws_client.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            s3_client = S3Client()
            client = s3_client.client
            
            assert client == mock_client
            mock_boto3.client.assert_called_once_with(
                's3',
                aws_access_key_id=s3_client.access_key_id,
                aws_secret_access_key=s3_client.secret_access_key,
                region_name=s3_client.region
            )
    
    def test_client_property_returns_same_client_on_subsequent_access(self):
        """Test that client property returns same client on subsequent access."""
        with patch('app.utils.aws_client.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            s3_client = S3Client()
            client1 = s3_client.client
            client2 = s3_client.client
            
            assert client1 == client2
            assert mock_boto3.client.call_count == 1


class TestS3ClientUploadFile:
    """Test cases for S3Client.upload_file method."""
    
    @pytest.fixture
    def s3_client(self):
        """Create S3Client instance for testing."""
        return S3Client(
            access_key_id="test_key",
            secret_access_key="test_secret",
            bucket_name="test_bucket",
            region="us-east-1"
        )
    
    @pytest.fixture
    def mock_file_obj(self):
        """Create mock file object."""
        return Mock()
    
    def test_upload_file_success(self, s3_client, mock_file_obj):
        """Test successful file upload."""
        mock_client = Mock()
        s3_client._client = mock_client
        
        result = s3_client.upload_file(
            file_obj=mock_file_obj,
            s3_key="test/key.txt",
            content_type="text/plain"
        )
        
        assert result == "test/key.txt"
        mock_client.upload_fileobj.assert_called_once()
    
    def test_upload_file_with_metadata(self, s3_client, mock_file_obj):
        """Test file upload with metadata."""
        mock_client = Mock()
        s3_client._client = mock_client
        metadata = {"key": "value"}
        
        s3_client.upload_file(
            file_obj=mock_file_obj,
            s3_key="test/key.txt",
            content_type="text/plain",
            metadata=metadata
        )
        
        call_args = mock_client.upload_fileobj.call_args
        assert call_args[1]['ExtraArgs']['Metadata'] == metadata
    
    def test_upload_file_without_content_type(self, s3_client, mock_file_obj):
        """Test file upload without content type."""
        mock_client = Mock()
        s3_client._client = mock_client
        
        s3_client.upload_file(
            file_obj=mock_file_obj,
            s3_key="test/key.txt"
        )
        
        call_args = mock_client.upload_fileobj.call_args
        extra_args = call_args[1].get('ExtraArgs')
        if extra_args:
            assert 'ContentType' not in extra_args
        else:
            assert extra_args is None
    
    def test_upload_file_raises_error_for_invalid_bucket(self, s3_client, mock_file_obj):
        """Test that upload raises error for invalid bucket name."""
        s3_client.bucket_name = "your_s3_bucket_name"
        
        with pytest.raises(ValueError, match=ErrorMessages.S3_BUCKET_REQUIRED):
            s3_client.upload_file(
                file_obj=mock_file_obj,
                s3_key="test/key.txt"
            )
    
    def test_upload_file_raises_error_for_empty_bucket(self, s3_client, mock_file_obj):
        """Test that upload raises error for empty bucket name."""
        s3_client.bucket_name = None
        
        with pytest.raises(ValueError, match=ErrorMessages.S3_BUCKET_REQUIRED):
            s3_client.upload_file(
                file_obj=mock_file_obj,
                s3_key="test/key.txt"
            )
    
    def test_upload_file_raises_error_for_invalid_access_key(self, s3_client, mock_file_obj):
        """Test that upload raises error for invalid access key."""
        s3_client.access_key_id = "your_aws_access_key_id"
        
        with pytest.raises(ValueError, match=ErrorMessages.AWS_ACCESS_KEY_REQUIRED):
            s3_client.upload_file(
                file_obj=mock_file_obj,
                s3_key="test/key.txt"
            )
    
    def test_upload_file_raises_error_for_empty_access_key(self, s3_client, mock_file_obj):
        """Test that upload raises error for empty access key."""
        s3_client.access_key_id = None
        
        with pytest.raises(ValueError, match=ErrorMessages.AWS_ACCESS_KEY_REQUIRED):
            s3_client.upload_file(
                file_obj=mock_file_obj,
                s3_key="test/key.txt"
            )
    
    def test_upload_file_handles_client_error(self, s3_client, mock_file_obj):
        """Test that upload handles ClientError."""
        mock_client = Mock()
        mock_client.upload_fileobj.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'UploadFile'
        )
        s3_client._client = mock_client
        
        with pytest.raises(ClientError):
            s3_client.upload_file(
                file_obj=mock_file_obj,
                s3_key="test/key.txt"
            )
    
    def test_upload_file_handles_boto_core_error(self, s3_client, mock_file_obj):
        """Test that upload handles BotoCoreError."""
        mock_client = Mock()
        mock_client.upload_fileobj.side_effect = BotoCoreError()
        s3_client._client = mock_client
        
        with pytest.raises(ValueError):  # BotoCoreError is re-raised as ValueError
            s3_client.upload_file(
                file_obj=mock_file_obj,
                s3_key="test/key.txt"
            )
    
    def test_upload_file_with_both_content_type_and_metadata(self, s3_client, mock_file_obj):
        """Test file upload with both content type and metadata."""
        mock_client = Mock()
        s3_client._client = mock_client
        metadata = {"key": "value"}
        
        s3_client.upload_file(
            file_obj=mock_file_obj,
            s3_key="test/key.txt",
            content_type="text/plain",
            metadata=metadata
        )
        
        call_args = mock_client.upload_fileobj.call_args
        extra_args = call_args[1]['ExtraArgs']
        assert extra_args['ContentType'] == "text/plain"
        assert extra_args['Metadata'] == metadata


class TestS3ClientDownloadFile:
    """Test cases for S3Client.download_file method."""
    
    @pytest.fixture
    def s3_client(self):
        """Create S3Client instance for testing."""
        return S3Client(
            access_key_id="test_key",
            secret_access_key="test_secret",
            bucket_name="test_bucket",
            region="us-east-1"
        )
    
    @pytest.fixture
    def mock_file_obj(self):
        """Create mock file object."""
        return Mock()
    
    def test_download_file_success(self, s3_client, mock_file_obj):
        """Test successful file download."""
        mock_client = Mock()
        s3_client._client = mock_client
        
        s3_client.download_file(
            s3_key="test/key.txt",
            file_obj=mock_file_obj
        )
        
        mock_client.download_fileobj.assert_called_once_with(
            s3_client.bucket_name,
            "test/key.txt",
            mock_file_obj
        )
    
    def test_download_file_handles_file_not_found(self, s3_client, mock_file_obj):
        """Test that download handles file not found error."""
        mock_client = Mock()
        mock_client.download_fileobj.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'File not found'}},
            'DownloadFile'
        )
        s3_client._client = mock_client
        
        with pytest.raises(ClientError):
            s3_client.download_file(
                s3_key="test/key.txt",
                file_obj=mock_file_obj
            )
    
    def test_download_file_handles_boto_core_error(self, s3_client, mock_file_obj):
        """Test that download handles BotoCoreError."""
        mock_client = Mock()
        mock_client.download_fileobj.side_effect = BotoCoreError()
        s3_client._client = mock_client
        
        with pytest.raises(ValueError):  # BotoCoreError is re-raised as ValueError
            s3_client.download_file(
                s3_key="test/key.txt",
                file_obj=mock_file_obj
            )


class TestS3ClientDeleteFile:
    """Test cases for S3Client.delete_file method."""
    
    @pytest.fixture
    def s3_client(self):
        """Create S3Client instance for testing."""
        return S3Client(
            access_key_id="test_key",
            secret_access_key="test_secret",
            bucket_name="test_bucket",
            region="us-east-1"
        )
    
    def test_delete_file_success(self, s3_client):
        """Test successful file deletion."""
        mock_client = Mock()
        s3_client._client = mock_client
        
        s3_client.delete_file("test/key.txt")
        
        mock_client.delete_object.assert_called_once_with(
            Bucket=s3_client.bucket_name,
            Key="test/key.txt"
        )
    
    def test_delete_file_handles_client_error(self, s3_client):
        """Test that delete handles ClientError."""
        mock_client = Mock()
        mock_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DeleteFile'
        )
        s3_client._client = mock_client
        
        with pytest.raises(ClientError):
            s3_client.delete_file("test/key.txt")


class TestS3ClientFileExists:
    """Test cases for S3Client.file_exists method."""
    
    @pytest.fixture
    def s3_client(self):
        """Create S3Client instance for testing."""
        return S3Client(
            access_key_id="test_key",
            secret_access_key="test_secret",
            bucket_name="test_bucket",
            region="us-east-1"
        )
    
    def test_file_exists_returns_true(self, s3_client):
        """Test that file_exists returns True when file exists."""
        mock_client = Mock()
        s3_client._client = mock_client
        
        result = s3_client.file_exists("test/key.txt")
        
        assert result is True
        mock_client.head_object.assert_called_once_with(
            Bucket=s3_client.bucket_name,
            Key="test/key.txt"
        )
    
    def test_file_exists_returns_false_for_404(self, s3_client):
        """Test that file_exists returns False for 404 error."""
        mock_client = Mock()
        mock_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not found'}},
            'FileExists'
        )
        s3_client._client = mock_client
        
        result = s3_client.file_exists("test/key.txt")
        
        assert result is False
    
    def test_file_exists_returns_false_for_no_such_key(self, s3_client):
        """Test that file_exists returns False for NoSuchKey error."""
        mock_client = Mock()
        mock_client.head_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Not found'}},
            'FileExists'
        )
        s3_client._client = mock_client
        
        result = s3_client.file_exists("test/key.txt")
        
        assert result is False


class TestS3ClientGetPresignedUrl:
    """Test cases for S3Client.get_presigned_url method."""
    
    @pytest.fixture
    def s3_client(self):
        """Create S3Client instance for testing."""
        return S3Client(
            access_key_id="test_key",
            secret_access_key="test_secret",
            bucket_name="test_bucket",
            region="us-east-1"
        )
    
    def test_get_presigned_url_success(self, s3_client):
        """Test successful presigned URL generation."""
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = "https://test-url.com"
        s3_client._client = mock_client
        
        result = s3_client.get_presigned_url("test/key.txt")
        
        assert result == "https://test-url.com"
        mock_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': s3_client.bucket_name, 'Key': 'test/key.txt'},
            ExpiresIn=3600
        )
    
    def test_get_presigned_url_with_custom_expiration(self, s3_client):
        """Test presigned URL generation with custom expiration."""
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = "https://test-url.com"
        s3_client._client = mock_client
        
        s3_client.get_presigned_url("test/key.txt", expiration=7200)
        
        call_args = mock_client.generate_presigned_url.call_args
        assert call_args[1]['ExpiresIn'] == 7200


class TestGetS3Client:
    """Test cases for get_s3_client function."""
    
    def test_get_s3_client_returns_s3_client_instance(self):
        """Test that get_s3_client returns S3Client instance."""
        with patch('app.utils.aws_client.S3Client') as mock_s3_client_class:
            mock_instance = Mock()
            mock_s3_client_class.return_value = mock_instance
            
            result = get_s3_client()
            
            assert result == mock_instance
            mock_s3_client_class.assert_called_once()

