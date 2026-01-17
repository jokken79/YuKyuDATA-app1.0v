"""Base ORM Model with common fields"""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base
from datetime import datetime
from uuid import uuid4
import uuid as uuid_module

Base = declarative_base()


class BaseModel:
    """
    Base model with common fields for all entities.

    Fields:
    - id: UUID primary key (unique across all tables)
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    """

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_module.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert model to dictionary for serialization."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        """String representation of model instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"
