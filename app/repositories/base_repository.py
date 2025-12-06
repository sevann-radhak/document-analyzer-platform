"""Base repository class with common CRUD operations."""
from typing import Generic, TypeVar, Optional, List, Type, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations for SQLAlchemy models."""
    
    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize base repository.
        
        Args:
            db: SQLAlchemy database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity ID
        
        Returns:
            Entity object if found, None otherwise
        """
        try:
            return self.db.query(self.model).filter(self.model.id == entity_id).first()
        except SQLAlchemyError:
            return None
    
    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by_field: Optional[str] = None
    ) -> List[T]:
        """
        List all entities with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            order_by_field: Field name to order by (defaults to created_at desc)
        
        Returns:
            List of entity objects
        """
        try:
            query = self.db.query(self.model)
            
            if order_by_field:
                order_field = getattr(self.model, order_by_field, None)
                if order_field:
                    query = query.order_by(desc(order_field))
            else:
                if hasattr(self.model, 'created_at'):
                    query = query.order_by(desc(self.model.created_at))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError:
            return []
    
    def count_all(self) -> int:
        """
        Count all entities.
        
        Returns:
            Total number of entities
        """
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError:
            return 0
    
    def delete(self, entity_id: int) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Entity ID to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                return False
            
            self.db.delete(entity)
            self.db.commit()
            return True
        except SQLAlchemyError:
            self.db.rollback()
            return False
    
    def _create_entity(self, **kwargs) -> T:
        """
        Internal method to create entity with common error handling.
        
        Args:
            **kwargs: Entity attributes
        
        Returns:
            Created entity object
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            entity = self.model(**kwargs)
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError:
            self.db.rollback()
            raise
    
    def _update_entity(
        self,
        entity_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Internal method to update entity with common error handling.
        
        Args:
            entity_id: Entity ID to update
            update_data: Dictionary with fields to update
        
        Returns:
            Updated entity object if found, None otherwise
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                return None
            
            for key, value in update_data.items():
                if value is not None and hasattr(entity, key):
                    setattr(entity, key, value)
            
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError:
            self.db.rollback()
            return None

