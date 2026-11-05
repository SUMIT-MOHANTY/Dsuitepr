"""Todo model with user relationship and priority levels."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.extensions import db

if TYPE_CHECKING:
    from .user import User


class PriorityLevel(str, PyEnum):
    """Priority levels for todo items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Todo(db.Model):
    """Todo model for task management.
    
    Attributes:
        id: UUID primary key
        user_id: Foreign key to User who owns this todo
        title: Todo title (max 200 chars, required)
        description: Optional detailed description
        is_completed: Completion status
        priority: Priority level (low/medium/high)
        due_date: Optional due date
        created_at: Creation timestamp
        updated_at: Last update timestamp
        completed_at: Timestamp when marked complete
    """
    
    __tablename__ = 'todos'
    
    # Composite index for common query patterns
    __table_args__ = (
        Index('idx_todos_user_completed', 'user_id', 'is_completed'),
        Index('idx_todos_user_priority', 'user_id', 'priority'),
        Index('idx_todos_due_date', 'due_date'),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=PriorityLevel.MEDIUM.value,
        nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="todos"
    )
    
    def mark_complete(self) -> None:
        """Mark the todo as completed."""
        self.is_completed = True
        self.completed_at = datetime.now(timezone.utc)
    
    def mark_incomplete(self) -> None:
        """Mark the todo as not completed."""
        self.is_completed = False
        self.completed_at = None
    
    def to_dict(self) -> dict:
        """Convert todo to dictionary representation.
        
        Returns:
            Dictionary with todo data
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'is_completed': self.is_completed,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self) -> str:
        """Return string representation of todo.
        
        Returns:
            String with todo ID and title
        """
        return f'<Todo {self.id}: {self.title[:30]}...>'
