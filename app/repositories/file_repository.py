"""File repository for database operations on File model."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.file import File
from app.repositories.base_repository import BaseRepository


class FileRepository(BaseRepository[File]):
    """Repository for File model operations."""
    
    def __init__(self, db: Session):
        """
        Initialize file repository.
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, File)
    
    def create(
        self,
        filename: str,
        s3_key: str,
        uploaded_by: int,
        validation_results: Optional[Dict[str, Any]] = None
    ) -> File:
        """
        Create a new file record.
        
        Args:
            filename: Original filename
            s3_key: S3 object key where file is stored
            uploaded_by: ID of user who uploaded the file
            validation_results: Optional validation results dictionary
        
        Returns:
            Created File object
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self._create_entity(
            filename=filename,
            s3_key=s3_key,
            uploaded_by=uploaded_by,
            validation_results=validation_results
        )
    
    
    def get_by_s3_key(self, s3_key: str) -> Optional[File]:
        """
        Get file by S3 key.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            File object if found, None otherwise
        """
        try:
            return self.db.query(File).filter(File.s3_key == s3_key).first()
        except SQLAlchemyError:
            return None
    
    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[File]:
        """
        Get all files uploaded by a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of File objects
        """
        try:
            return (
                self.db.query(File)
                .filter(File.uploaded_by == user_id)
                .order_by(File.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError:
            return []
    
    
    def update(
        self,
        file_id: int,
        filename: Optional[str] = None,
        validation_results: Optional[Dict[str, Any]] = None
    ) -> Optional[File]:
        """
        Update file record.
        
        Args:
            file_id: File ID to update
            filename: New filename (optional)
            validation_results: New validation results (optional)
        
        Returns:
            Updated File object if found, None otherwise
        """
        update_data = {}
        if filename is not None:
            update_data['filename'] = filename
        if validation_results is not None:
            update_data['validation_results'] = validation_results
        
        return self._update_entity(file_id, update_data)
    
    
    def count_by_user(self, user_id: int) -> int:
        """
        Count files uploaded by a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of files uploaded by user
        """
        try:
            return (
                self.db.query(File)
                .filter(File.uploaded_by == user_id)
                .count()
            )
        except SQLAlchemyError:
            return 0
    
    def exists_by_s3_key(self, s3_key: str) -> bool:
        """
        Check if file exists by S3 key.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if file exists, False otherwise
        """
        try:
            return (
                self.db.query(File)
                .filter(File.s3_key == s3_key)
                .first() is not None
            )
        except SQLAlchemyError:
            return False

