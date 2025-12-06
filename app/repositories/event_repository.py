"""Event repository for database operations on Event model."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.event import Event


class EventRepository:
    """Repository for Event model operations."""
    
    def __init__(self, db: Session):
        """
        Initialize event repository.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        event_type: str,
        description: str,
        user_id: Optional[int] = None
    ) -> Event:
        """
        Create a new event record.
        
        Args:
            event_type: Type of event (e.g., "Document upload", "AI", "User interaction")
            description: Event description
            user_id: Optional user ID associated with the event
        
        Returns:
            Created Event object
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            event = Event(
                event_type=event_type,
                description=description,
                user_id=user_id
            )
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except SQLAlchemyError:
            self.db.rollback()
            raise

