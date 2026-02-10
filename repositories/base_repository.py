"""Base Repository with common CRUD operations"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from datetime import datetime, timezone

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic base repository with common CRUD operations.

    This class provides:
    - CRUD operations (Create, Read, Update, Delete)
    - Filtering and searching
    - Pagination
    - Sorting

    Subclasses should override entity_class and optionally add specific queries.
    """

    def __init__(self, session: Session, entity_class: type):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
            entity_class: ORM model class (e.g., Employee, LeaveRequest)
        """
        self.session = session
        self.entity_class = entity_class

    def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        return self.session.get(self.entity_class, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        return self.session.query(self.entity_class).offset(skip).limit(limit).all()

    def count(self) -> int:
        """Get total count of entities."""
        return self.session.query(self.entity_class).count()

    def create(self, **kwargs) -> T:
        """Create new entity."""
        entity = self.entity_class(**kwargs)
        self.session.add(entity)
        self.session.flush()  # Get ID without commit
        return entity

    def update(self, id: str, **kwargs) -> Optional[T]:
        """Update entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return None

        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        # Update timestamp
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.now(timezone.utc)

        self.session.flush()
        return entity

    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return False

        self.session.delete(entity)
        self.session.flush()
        return True

    def save(self, entity: T) -> T:
        """Save entity (add or merge)."""
        self.session.merge(entity)
        self.session.flush()
        return entity

    def save_all(self, entities: List[T]) -> List[T]:
        """Save multiple entities."""
        for entity in entities:
            self.session.merge(entity)
        self.session.flush()
        return entities

    def commit(self):
        """Commit changes to database."""
        self.session.commit()

    def rollback(self):
        """Rollback changes."""
        self.session.rollback()

    def search(self, filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[T]:
        """
        Search entities by filters.

        Args:
            filters: Dict of column_name: value pairs
            skip: Offset for pagination
            limit: Limit for pagination

        Returns:
            List of matching entities
        """
        query = self.session.query(self.entity_class)

        for key, value in filters.items():
            if hasattr(self.entity_class, key):
                if value is not None:
                    query = query.filter(getattr(self.entity_class, key) == value)

        return query.offset(skip).limit(limit).all()

    def search_count(self, filters: Dict[str, Any]) -> int:
        """Count entities matching filters."""
        query = self.session.query(self.entity_class)

        for key, value in filters.items():
            if hasattr(self.entity_class, key):
                if value is not None:
                    query = query.filter(getattr(self.entity_class, key) == value)

        return query.count()

    def exists(self, **kwargs) -> bool:
        """Check if entity with given attributes exists."""
        return self.search(kwargs, limit=1) != []

    def get_ordered(
        self,
        order_by_field: str,
        ascending: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """Get entities ordered by field."""
        query = self.session.query(self.entity_class)

        if hasattr(self.entity_class, order_by_field):
            if ascending:
                query = query.order_by(getattr(self.entity_class, order_by_field))
            else:
                query = query.order_by(desc(getattr(self.entity_class, order_by_field)))

        return query.offset(skip).limit(limit).all()

    def bulk_create(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities efficiently.

        Note: For very large bulk operations, consider raw SQL INSERT.
        """
        self.session.add_all(entities)
        self.session.flush()
        return entities

    def bulk_delete(self, ids: List[str]) -> int:
        """Delete multiple entities by IDs."""
        count = self.session.query(self.entity_class).filter(
            self.entity_class.id.in_(ids)
        ).delete()
        self.session.flush()
        return count
