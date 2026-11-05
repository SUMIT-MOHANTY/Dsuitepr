"""Pydantic schemas for Todo model validation and serialization."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.todo import PriorityLevel


class TodoBase(BaseModel):
    """Base todo schema with common attributes."""
    
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(..., min_length=1, max_length=200, description="Todo title")
    description: Optional[str] = Field(None, max_length=2000, description="Optional todo description")
    priority: PriorityLevel = Field(PriorityLevel.MEDIUM, description="Todo priority level")
    due_date: Optional[datetime] = Field(None, description="Optional due date")


class TodoCreate(TodoBase):
    """Schema for creating a new todo.
    
    Attributes:
        title: Todo title (1-200 characters, required)
        description: Optional description (max 2000 characters)
        priority: Priority level (low, medium, high), defaults to medium
        due_date: Optional due date
    """
    
    pass


class TodoUpdate(BaseModel):
    """Schema for updating an existing todo.
    
    All fields are optional to allow partial updates.
    
    Attributes:
        title: New todo title (1-200 characters)
        description: New description (max 2000 characters)
        priority: New priority level
        due_date: New due date
        is_completed: Completion status
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New todo title")
    description: Optional[str] = Field(None, max_length=2000, description="New description")
    priority: Optional[PriorityLevel] = Field(None, description="New priority level")
    due_date: Optional[datetime] = Field(None, description="New due date")
    is_completed: Optional[bool] = Field(None, description="Completion status")


class TodoResponse(TodoBase):
    """Schema for todo response data.
    
    Attributes:
        id: Todo UUID
        user_id: Owner's user UUID
        is_completed: Whether the todo is completed
        created_at: Creation timestamp
        updated_at: Last update timestamp
        completed_at: Completion timestamp (null if not completed)
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Todo UUID")
    user_id: str = Field(..., description="Owner's user UUID")
    is_completed: bool = Field(..., description="Whether the todo is completed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class TodoListResponse(BaseModel):
    """Schema for paginated todo list response.
    
    Attributes:
        items: List of todo items
        total: Total number of todos matching the query
        page: Current page number
        per_page: Number of items per page
        pages: Total number of pages
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    items: List[TodoResponse] = Field(..., description="List of todo items")
    total: int = Field(..., description="Total number of todos matching the query")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class TodoStats(BaseModel):
    """Schema for todo statistics.
    
    Attributes:
        total: Total number of todos
        completed: Number of completed todos
        pending: Number of pending todos
        completion_rate: Percentage of completed todos (0-100)
        by_priority: Count breakdown by priority level
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    total: int = Field(..., description="Total number of todos")
    completed: int = Field(..., description="Number of completed todos")
    pending: int = Field(..., description="Number of pending todos")
    completion_rate: float = Field(..., ge=0, le=100, description="Percentage of completed todos")
    by_priority: dict = Field(default_factory=dict, description="Count breakdown by priority level")


class TodoBulkUpdate(BaseModel):
    """Schema for bulk todo operations.
    
    Attributes:
        ids: List of todo IDs to update
        is_completed: New completion status to apply
        priority: New priority to apply (optional)
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    ids: List[str] = Field(..., min_length=1, description="List of todo IDs to update")
    is_completed: Optional[bool] = Field(None, description="New completion status")
    priority: Optional[PriorityLevel] = Field(None, description="New priority level")


class TodoBulkDelete(BaseModel):
    """Schema for bulk todo deletion.
    
    Attributes:
        ids: List of todo IDs to delete
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    ids: List[str] = Field(..., min_length=1, description="List of todo IDs to delete")


class TodoFilterParams(BaseModel):
    """Schema for todo query filter parameters.
    
    Attributes:
        status: Filter by status (all, active, completed)
        priority: Filter by priority level
        search: Search in title and description
        sort_by: Sort field (created_at, updated_at, due_date, priority)
        sort_order: Sort order (asc, desc)
        page: Page number for pagination
        per_page: Items per page (max 100)
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[str] = Field(None, description="Filter by status: all, active, completed")
    priority: Optional[PriorityLevel] = Field(None, description="Filter by priority level")
    search: Optional[str] = Field(None, description="Search in title and description")
    sort_by: str = Field("created_at", description="Sort field: created_at, updated_at, due_date, priority")
    sort_order: str = Field("desc", description="Sort order: asc, desc")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status filter value."""
        if v is None:
            return v
        allowed = {'all', 'active', 'completed'}
        if v.lower() not in allowed:
            raise ValueError(f'Status must be one of: {", ".join(allowed)}')
        return v.lower()
    
    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort_by field."""
        allowed = {'created_at', 'updated_at', 'due_date', 'priority', 'title'}
        if v.lower() not in allowed:
            raise ValueError(f'Sort by must be one of: {", ".join(allowed)}')
        return v.lower()
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort_order value."""
        allowed = {'asc', 'desc'}
        if v.lower() not in allowed:
            raise ValueError(f'Sort order must be one of: {", ".join(allowed)}')
        return v.lower()
