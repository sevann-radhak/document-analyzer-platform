"""Event service for logging and retrieving application events."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.event_repository import EventRepository
from app.models.event import Event


class EventType:
    """Event type constants."""
    DOCUMENT_UPLOAD = "Document upload"
    AI = "AI"
    USER_INTERACTION = "User interaction"


def create_event(
    db: Session,
    event_type: str,
    description: str,
    user_id: Optional[int] = None
) -> Event:
    """
    Create a new event.
    
    Args:
        db: Database session
        event_type: Type of event (use EventType constants)
        description: Event description
        user_id: Optional user ID associated with the event
    
    Returns:
        Created Event object
    
    Raises:
        SQLAlchemyError: If database operation fails
    """
    event_repo = EventRepository(db)
    return event_repo.create(
        event_type=event_type,
        description=description,
        user_id=user_id
    )


def get_event_by_id(
    db: Session,
    event_id: int
) -> Optional[Event]:
    """
    Get event by ID.
    
    Args:
        db: Database session
        event_id: Event ID
    
    Returns:
        Event object if found, None otherwise
    """
    event_repo = EventRepository(db)
    return event_repo.get_by_id(event_id)


def get_events(
    db: Session,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Event]:
    """
    Get events with optional filtering.
    
    Args:
        db: Database session
        event_type: Optional event type filter
        user_id: Optional user ID filter
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of Event objects
    """
    event_repo = EventRepository(db)
    return event_repo.get_events(
        event_type=event_type,
        user_id=user_id,
        skip=skip,
        limit=limit
    )


def log_document_upload(
    db: Session,
    filename: str,
    classification: str,
    document_id: int,
    user_id: Optional[int] = None
) -> Event:
    """
    Log a document upload event.
    
    Args:
        db: Database session
        filename: Name of the uploaded document
        classification: Document classification (Invoice or Information)
        document_id: ID of the created document
        user_id: Optional user ID who uploaded the document
    
    Returns:
        Created Event object
    """
    description = (
        f"Document '{filename}' uploaded and classified as '{classification}'. "
        f"Document ID: {document_id}"
    )
    
    return create_event(
        db=db,
        event_type=EventType.DOCUMENT_UPLOAD,
        description=description,
        user_id=user_id
    )


def log_ai_classification(
    db: Session,
    filename: str,
    classification: str,
    user_id: Optional[int] = None
) -> Event:
    """
    Log an AI classification event.
    
    Args:
        db: Database session
        filename: Name of the document
        classification: Document classification result
        user_id: Optional user ID
    
    Returns:
        Created Event object
    """
    description = (
        f"AI classified document '{filename}' as '{classification}'"
    )
    
    return create_event(
        db=db,
        event_type=EventType.AI,
        description=description,
        user_id=user_id
    )


def log_user_interaction(
    db: Session,
    description: str,
    user_id: Optional[int] = None
) -> Event:
    """
    Log a user interaction event.
    
    Args:
        db: Database session
        description: Description of the user interaction
        user_id: Optional user ID
    
    Returns:
        Created Event object
    """
    return create_event(
        db=db,
        event_type=EventType.USER_INTERACTION,
        description=description,
        user_id=user_id
    )

