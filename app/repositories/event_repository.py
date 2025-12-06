"""Event repository for database operations on Event model."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_
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
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events with optional filtering.
        
        Args:
            event_type: Optional event type filter (exact match)
            user_id: Optional user ID filter
            description: Optional description filter (partial match, case-insensitive)
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
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
            
            if description:
                query = query.filter(Event.description.ilike(f"%{description}%"))
            
            if start_date:
                query = query.filter(Event.created_at >= start_date)
            
            if end_date:
                query = query.filter(Event.created_at <= end_date)
            
            return (
                query
                .order_by(Event.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError:
            return []
    
    def list_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        List all events with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of Event objects
        """
        try:
            return (
                self.db.query(Event)
                .order_by(Event.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError:
            return []
    
    def update(
        self,
        event_id: int,
        event_type: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Optional[Event]:
        """
        Update event record.
        
        Args:
            event_id: Event ID to update
            event_type: New event type (optional)
            description: New description (optional)
            user_id: New user ID (optional)
        
        Returns:
            Updated Event object if found, None otherwise
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            event = self.get_by_id(event_id)
            if not event:
                return None
            
            if event_type is not None:
                event.event_type = event_type
            if description is not None:
                event.description = description
            if user_id is not None:
                event.user_id = user_id
            
            self.db.commit()
            self.db.refresh(event)
            return event
        except SQLAlchemyError:
            self.db.rollback()
            return None
    
    def delete(self, event_id: int) -> bool:
        """
        Delete event record.
        
        Args:
            event_id: Event ID to delete
        
        Returns:
            True if deleted successfully, False otherwise
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            event = self.get_by_id(event_id)
            if not event:
                return False
            
            self.db.delete(event)
            self.db.commit()
            return True
        except SQLAlchemyError:
            self.db.rollback()
            return False
    
    def count_all(self) -> int:
        """
        Count all events.
        
        Returns:
            Total number of events
        """
        try:
            return self.db.query(Event).count()
        except SQLAlchemyError:
            return 0
    
    def count_by_type(self, event_type: str) -> int:
        """
        Count events by type.
        
        Args:
            event_type: Event type to count
        
        Returns:
            Number of events with the specified type
        """
        try:
            return (
                self.db.query(Event)
                .filter(Event.event_type == event_type)
                .count()
            )
        except SQLAlchemyError:
            return 0
    
    def count_by_user(self, user_id: int) -> int:
        """
        Count events by user ID.
        
        Args:
            user_id: User ID to count events for
        
        Returns:
            Number of events for the specified user
        """
        try:
            return (
                self.db.query(Event)
                .filter(Event.user_id == user_id)
                .count()
            )
        except SQLAlchemyError:
            return 0
    
    def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        """
        Get events within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of Event objects within the date range
        """
        try:
            return (
                self.db.query(Event)
                .filter(
                    and_(
                        Event.created_at >= start_date,
                        Event.created_at <= end_date
                    )
                )
                .order_by(Event.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError:
            return []
    
    def count_with_filters(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count events matching the filters.
        
        Args:
            event_type: Optional event type filter
            user_id: Optional user ID filter
            description: Optional description filter (partial match)
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
        
        Returns:
            Total number of events matching the filters
        """
        try:
            query = self.db.query(Event)
            
            if event_type:
                query = query.filter(Event.event_type == event_type)
            
            if user_id:
                query = query.filter(Event.user_id == user_id)
            
            if description:
                query = query.filter(Event.description.ilike(f"%{description}%"))
            
            if start_date:
                query = query.filter(Event.created_at >= start_date)
            
            if end_date:
                query = query.filter(Event.created_at <= end_date)
            
            return query.count()
        except SQLAlchemyError:
            return 0

