"""Pydantic schemas for request/response validation and serialization.

This module exports all schema classes for use throughout the application.
Schemas are organized by domain (user, todo) and follow Pydantic v2 patterns.
"""

# User schemas
from backend.app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserProfile,
)

# Todo schemas
from backend.app.schemas.todo import (
    TodoBase,
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoListResponse,
    TodoStats,
    TodoBulkUpdate,
    TodoBulkDelete,
    TodoFilterParams,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    # Todo schemas
    "TodoBase",
    "TodoCreate",
    "TodoUpdate",
    "TodoResponse",
    "TodoListResponse",
    "TodoStats",
    "TodoBulkUpdate",
    "TodoBulkDelete",
    "TodoFilterParams",
]
