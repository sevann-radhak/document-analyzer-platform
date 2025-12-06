"""AWS S3 client utility for file operations."""
import boto3
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError, BotoCoreError
from botocore.client import BaseClient
from app.core.config import settings


class S3Client:
    """AWS S3 client wrapper for file operations."""
    
    def __init__(
        self,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize S3 client.
        
        Args:
            access_key_id: AWS access key ID (defaults to settings)
            secret_access_key: AWS secret access key (defaults to settings)
            bucket_name: S3 bucket name (defaults to settings)
            region: AWS region (defaults to settings)
        """
        self.access_key_id = access_key_id or settings.aws_access_key_id
        self.secret_access_key = secret_access_key or settings.aws_secret_access_key
        self.bucket_name = bucket_name or settings.aws_s3_bucket_name
        self.region = region or settings.aws_region
        
        self._client: Optional[BaseClient] = None
    
    @property
    def client(self) -> BaseClient:
        """Get or create S3 client instance."""
        if self._client is None:
            self._client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region
            )
        return self._client
    
    def upload_file(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file to S3 bucket.
        
        Args:
            file_obj: File-like object to upload
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the file
            metadata: Optional metadata dictionary
        
        Returns:
            S3 object key (s3_key)
        
        Raises:
            ValueError: If bucket name or credentials are invalid
            ClientError: If AWS S3 operation fails
            BotoCoreError: If boto3 operation fails
        """
        if not self.bucket_name or self.bucket_name == "your_s3_bucket_name":
            raise ValueError("S3 bucket name must be configured in settings")
        
        if not self.access_key_id or self.access_key_id == "your_aws_access_key_id":
            raise ValueError("AWS access key ID must be configured in settings")
        
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args if extra_args else None
            )
            return s3_key
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': str(e)}},
                operation_name='UploadFile'
            ) from e
        except BotoCoreError as e:
            raise BotoCoreError(f"Boto3 error during file upload: {str(e)}") from e
    
    def download_file(self, s3_key: str, file_obj: BinaryIO) -> None:
        """
        Download a file from S3 bucket.
        
        Args:
            s3_key: S3 object key (path in bucket)
            file_obj: File-like object to write to
        
        Raises:
            ValueError: If bucket name or credentials are invalid
            ClientError: If AWS S3 operation fails (e.g., file not found)
            BotoCoreError: If boto3 operation fails
        """
        if not self.bucket_name or self.bucket_name == "your_s3_bucket_name":
            raise ValueError("S3 bucket name must be configured in settings")
        
        if not self.access_key_id or self.access_key_id == "your_aws_access_key_id":
            raise ValueError("AWS access key ID must be configured in settings")
        
        try:
            self.client.download_fileobj(self.bucket_name, s3_key, file_obj)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                raise ClientError(
                    error_response={'Error': {'Code': 'NoSuchKey', 'Message': f'File {s3_key} not found in bucket'}},
                    operation_name='DownloadFile'
                ) from e
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': str(e)}},
                operation_name='DownloadFile'
            ) from e
        except BotoCoreError as e:
            raise BotoCoreError(f"Boto3 error during file download: {str(e)}") from e
    
    def delete_file(self, s3_key: str) -> None:
        """
        Delete a file from S3 bucket.
        
        Args:
            s3_key: S3 object key (path in bucket)
        
        Raises:
            ValueError: If bucket name or credentials are invalid
            ClientError: If AWS S3 operation fails
            BotoCoreError: If boto3 operation fails
        """
        if not self.bucket_name or self.bucket_name == "your_s3_bucket_name":
            raise ValueError("S3 bucket name must be configured in settings")
        
        if not self.access_key_id or self.access_key_id == "your_aws_access_key_id":
            raise ValueError("AWS access key ID must be configured in settings")
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': str(e)}},
                operation_name='DeleteFile'
            ) from e
        except BotoCoreError as e:
            raise BotoCoreError(f"Boto3 error during file deletion: {str(e)}") from e
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3 bucket.
        
        Args:
            s3_key: S3 object key (path in bucket)
        
        Returns:
            True if file exists, False otherwise
        
        Raises:
            ValueError: If bucket name or credentials are invalid
            ClientError: If AWS S3 operation fails
            BotoCoreError: If boto3 operation fails
        """
        if not self.bucket_name or self.bucket_name == "your_s3_bucket_name":
            raise ValueError("S3 bucket name must be configured in settings")
        
        if not self.access_key_id or self.access_key_id == "your_aws_access_key_id":
            raise ValueError("AWS access key ID must be configured in settings")
        
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404' or error_code == 'NoSuchKey':
                return False
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': str(e)}},
                operation_name='FileExists'
            ) from e
        except BotoCoreError as e:
            raise BotoCoreError(f"Boto3 error during file existence check: {str(e)}") from e
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary file access.
        
        Args:
            s3_key: S3 object key (path in bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL string
        
        Raises:
            ValueError: If bucket name or credentials are invalid
            ClientError: If AWS S3 operation fails
            BotoCoreError: If boto3 operation fails
        """
        if not self.bucket_name or self.bucket_name == "your_s3_bucket_name":
            raise ValueError("S3 bucket name must be configured in settings")
        
        if not self.access_key_id or self.access_key_id == "your_aws_access_key_id":
            raise ValueError("AWS access key ID must be configured in settings")
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': str(e)}},
                operation_name='GeneratePresignedUrl'
            ) from e
        except BotoCoreError as e:
            raise BotoCoreError(f"Boto3 error during presigned URL generation: {str(e)}") from e


def get_s3_client() -> S3Client:
    """Get a configured S3 client instance."""
    return S3Client()

