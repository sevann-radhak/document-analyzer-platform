"""Event service for logging application events."""
from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.event_repository import EventRepository


class EventType:
    """Event type constants."""
    DOCUMENT_UPLOAD = "Document upload"
    AI = "AI"
    USER_INTERACTION = "User interaction"


def log_document_upload(
    db: Session,
    filename: str,
    classification: str,
    document_id: int,
    user_id: Optional[int] = None
) -> None:
    """
    Log a document upload event.
    
    Args:
        db: Database session
        filename: Name of the uploaded document
        classification: Document classification (Invoice or Information)
        document_id: ID of the created document
        user_id: Optional user ID who uploaded the document
    """
    event_repo = EventRepository(db)
    
    description = (
        f"Document '{filename}' uploaded and classified as '{classification}'. "
        f"Document ID: {document_id}"
    )
    
    event_repo.create(
        event_type=EventType.DOCUMENT_UPLOAD,
        description=description,
        user_id=user_id
    )


def log_ai_classification(
    db: Session,
    filename: str,
    classification: str,
    user_id: Optional[int] = None
) -> None:
    """
    Log an AI classification event.
    
    Args:
        db: Database session
        filename: Name of the document
        classification: Document classification result
        user_id: Optional user ID
    """
    event_repo = EventRepository(db)
    
    description = (
        f"AI classified document '{filename}' as '{classification}'"
    )
    
    event_repo.create(
        event_type=EventType.AI,
        description=description,
        user_id=user_id
    )

