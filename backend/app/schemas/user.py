"""Pydantic schemas for User model validation and serialization."""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    
    model_config = ConfigDict(
        from_attributes=True,
        extra='forbid',  # Strict mode: reject extra fields
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_assignment=True  # Validate on assignment
    )
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=80,
        description="Unique username",
        pattern=r'^[a-zA-Z0-9_]+$'  # Alphanumeric and underscore only
    )
    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for user registration.
    
    Attributes:
        username: Unique username (3-80 characters, alphanumeric and underscore)
        email: Valid email address
        password: Password (8-128 characters, must contain uppercase, lowercase, digit)
    """
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        """Validate username contains only allowed characters."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        if v[0].isdigit():
            raise ValueError('Username must not start with a digit')
        return v.lower()  # Normalize to lowercase
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum strength requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
        return v


class UserLogin(BaseModel):
    """Schema for user login.
    
    Attributes:
        username: Username or email for login
        password: User password
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        extra='forbid',
        str_strip_whitespace=True
    )
    
    username: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Username or email"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User password"
    )


class UserUpdate(BaseModel):
    """Schema for updating user information.
    
    All fields are optional to allow partial updates.
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        extra='forbid',
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=80,
        description="New username",
        pattern=r'^[a-zA-Z0-9_]+$'
    )
    email: Optional[EmailStr] = Field(None, description="New email address")
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="New password"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate username contains only allowed characters."""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        if v[0].isdigit():
            raise ValueError('Username must not start with a digit')
        return v.lower()  # Normalize to lowercase
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        """Validate password meets minimum strength requirements if provided."""
        if v is None:
            return v
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
        return v


class UserResponse(BaseModel):
    """Schema for user response data (excludes sensitive fields).
    
    Attributes:
        id: User UUID
        username: User's username
        email: User's email address
        is_active: Whether the user account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        extra='forbid'
    )
    
    id: str = Field(..., description="User UUID")
    username: str = Field(..., description="User's username")
    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserProfile(UserResponse):
    """Extended user profile with additional statistics."""
    
    model_config = ConfigDict(
        from_attributes=True,
        extra='forbid'
    )
    
    todo_count: int = Field(0, ge=0, description="Total number of todos")
    completed_count: int = Field(0, ge=0, description="Number of completed todos")
    pending_count: int = Field(0, ge=0, description="Number of pending todos")
