"""User model with password hashing and authentication."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash

from backend.app.extensions import db

if TYPE_CHECKING:
    from .todo import Todo


class User(db.Model):
    """User model for authentication and todo ownership.
    
    Attributes:
        id: UUID primary key
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password (bcrypt)
        is_active: Whether the account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'users'
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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
    
    # Relationships
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def set_password(self, password: str) -> None:
        """Hash and set the user password.
        
        Args:
            password: Plain text password to hash
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def get_id(self) -> str:
        """Return the user ID for Flask-Login.
        
        Returns:
            User ID as string
        """
        return self.id
    
    @property
    def is_authenticated(self) -> bool:
        """Return True if user is authenticated.
        
        Returns:
            Always True for valid user instances
        """
        return True
    
    @property
    def is_anonymous(self) -> bool:
        """Return False as this is a real user.
        
        Returns:
            Always False for valid user instances
        """
        return False
    
    def to_dict(self) -> dict:
        """Convert user to dictionary representation.
        
        Returns:
            Dictionary with user data (excluding sensitive fields)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        """Return string representation of user.
        
        Returns:
            String with user ID and username
        """
        return f'<User {self.id}: {self.username}>'
