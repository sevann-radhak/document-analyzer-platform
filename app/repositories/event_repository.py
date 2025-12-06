"""Event repository for database operations on Event model."""
from typing import Optional, List
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
    
    def get_by_id(self, event_id: int) -> Optional[Event]:
        """
        Get event by ID.
        
        Args:
            event_id: Event ID
        
        Returns:
            Event object if found, None otherwise
        """
        try:
            return self.db.query(Event).filter(Event.id == event_id).first()
        except SQLAlchemyError:
            return None
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events with optional filtering.
        
        Args:
            event_type: Optional event type filter
            user_id: Optional user ID filter
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of Event objects
        """
        try:
            query = self.db.query(Event)
            
            if event_type:
                query = query.filter(Event.event_type == event_type)
            
            if user_id:
                query = query.filter(Event.user_id == user_id)
            
            return (
                query
                .order_by(Event.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError:
            return []

