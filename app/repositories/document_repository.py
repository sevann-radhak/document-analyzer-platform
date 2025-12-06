"""Document repository for database operations on Document model."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document model operations."""
    
    def __init__(self, db: Session):
        """
        Initialize document repository.
        
        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Document)
    
    def create(
        self,
        filename: str,
        file_type: str,
        s3_key: str,
        classification: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Create a new document record.
        
        Args:
            filename: Original filename
            file_type: File type (PDF, JPG, PNG)
            s3_key: S3 object key where file is stored
            classification: Document classification (Invoice or Information)
            extracted_data: Optional extracted data dictionary
        
        Returns:
            Created Document object
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        return self._create_entity(
            filename=filename,
            file_type=file_type,
            s3_key=s3_key,
            classification=classification,
            extracted_data=extracted_data
        )
    
    
    def get_by_s3_key(self, s3_key: str) -> Optional[Document]:
        """
        Get document by S3 key.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Document object if found, None otherwise
        """
        try:
            return self.db.query(Document).filter(Document.s3_key == s3_key).first()
        except SQLAlchemyError:
            return None
    
    
    def get_by_classification(
        self,
        classification: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """
        Get documents by classification.
        
        Args:
            classification: Document classification (Invoice or Information)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of Document objects
        """
        try:
            return (
                self.db.query(Document)
                .filter(Document.classification == classification)
                .order_by(Document.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError:
            return []
    
    def get_by_file_type(
        self,
        file_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """
        Get documents by file type.
        
        Args:
            file_type: File type (PDF, JPG, PNG)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of Document objects
        """
        try:
            return (
                self.db.query(Document)
                .filter(Document.file_type == file_type)
                .order_by(Document.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError:
            return []
    
    def update(
        self,
        document_id: int,
        filename: Optional[str] = None,
        classification: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Document]:
        """
        Update document record.
        
        Args:
            document_id: Document ID to update
            filename: New filename (optional)
            classification: New classification (optional)
            extracted_data: New extracted data (optional)
        
        Returns:
            Updated Document object if found, None otherwise
        """
        update_data = {}
        if filename is not None:
            update_data['filename'] = filename
        if classification is not None:
            update_data['classification'] = classification
        if extracted_data is not None:
            update_data['extracted_data'] = extracted_data
        
        return self._update_entity(document_id, update_data)
    
    
    
    def count_by_classification(self, classification: str) -> int:
        """
        Count documents by classification.
        
        Args:
            classification: Document classification (Invoice or Information)
        
        Returns:
            Number of documents with the classification
        """
        try:
            return (
                self.db.query(Document)
                .filter(Document.classification == classification)
                .count()
            )
        except SQLAlchemyError:
            return 0
    
    def exists_by_s3_key(self, s3_key: str) -> bool:
        """
        Check if document exists by S3 key.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if document exists, False otherwise
        """
        try:
            return (
                self.db.query(Document)
                .filter(Document.s3_key == s3_key)
                .first() is not None
            )
        except SQLAlchemyError:
            return False

