"""Todo service layer for business logic operations."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import or_, func

from backend.app.extensions import db
from backend.app.models.todo import Todo, PriorityLevel
from backend.app.schemas.todo import (
    TodoCreate,
    TodoUpdate,
    TodoFilterParams,
)


class TodoService:
    """Service class for todo business logic operations."""
    
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    @staticmethod
    def create_todo(user_id: str, todo_data: TodoCreate) -> Todo:
        """Create a new todo item.
        
        Args:
            user_id: The ID of the user creating the todo
            todo_data: Validated todo creation data
            
        Returns:
            The newly created Todo instance
        """
        todo = Todo(
            user_id=user_id,
            title=todo_data.title,
            description=todo_data.description,
            priority=todo_data.priority.value,
            due_date=todo_data.due_date,
            is_completed=False
        )
        
        db.session.add(todo)
        db.session.commit()
        
        return todo
    
    @staticmethod
    def get_todo(todo_id: str, user_id: str) -> Optional[Todo]:
        """Get a single todo by ID with user ownership check.
        
        Args:
            todo_id: The UUID of the todo
            user_id: The UUID of the requesting user
            
        Returns:
            The Todo if found and owned by user, None otherwise
        """
        return Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    @staticmethod
    def update_todo(todo: Todo, update_data: TodoUpdate) -> Todo:
        """Update a todo with the provided data.
        
        Args:
            todo: The Todo instance to update
            update_data: Validated update data
            
        Returns:
            The updated Todo instance
        """
        # Track if completion status is changing
        was_completed = todo.is_completed
        
        if update_data.title is not None:
            todo.title = update_data.title
            
        if update_data.description is not None:
            todo.description = update_data.description
            
        if update_data.priority is not None:
            todo.priority = update_data.priority.value
            
        if update_data.due_date is not None:
            todo.due_date = update_data.due_date
            
        if update_data.is_completed is not None:
            if update_data.is_completed and not was_completed:
                todo.mark_complete()
            elif not update_data.is_completed and was_completed:
                todo.mark_incomplete()
        
        todo.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return todo
    
    @staticmethod
    def delete_todo(todo: Todo) -> None:
        """Delete a todo.
        
        Args:
            todo: The Todo instance to delete
        """
        db.session.delete(todo)
        db.session.commit()
    
    @staticmethod
    def list_todos(
        user_id: str,
        filter_params: Optional[TodoFilterParams] = None,
        page: int = 1,
        per_page: int = DEFAULT_PAGE_SIZE
    ) -> Tuple[List[Todo], int]:
        """Get paginated list of todos for a user with optional filtering.
        
        Args:
            user_id: The user's UUID
            filter_params: Optional filter parameters
            page: Page number (1-indexed)
            per_page: Items per page (capped at MAX_PAGE_SIZE)
            
        Returns:
            Tuple of (list of todos, total count)
        """
        # Validate and cap pagination
        page = max(1, page)
        per_page = min(per_page, TodoService.MAX_PAGE_SIZE)
        per_page = max(1, per_page)
        
        # Build base query
        query = Todo.query.filter_by(user_id=user_id)
        
        # Apply filters if provided
        if filter_params:
            query = TodoService._apply_filters(query, filter_params)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        todos = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return todos, total
    
    @staticmethod
    def _apply_filters(query, filter_params: TodoFilterParams):
        """Apply filters to a todo query.
        
        Args:
            query: Base SQLAlchemy query
            filter_params: Filter parameters
            
        Returns:
            Filtered query
        """
        # Status filter
        if filter_params.status:
            if filter_params.status == 'active':
                query = query.filter_by(is_completed=False)
            elif filter_params.status == 'completed':
                query = query.filter_by(is_completed=True)
        
        # Priority filter
        if filter_params.priority:
            query = query.filter_by(priority=filter_params.priority.value)
        
        # Search filter
        if filter_params.search:
            search_term = f"%{filter_params.search}%"
            query = query.filter(
                or_(
                    Todo.title.ilike(search_term),
                    Todo.description.ilike(search_term)
                )
            )
        
        # Sorting
        sort_column = getattr(Todo, filter_params.sort_by, Todo.created_at)
        if filter_params.sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        return query
    
    @staticmethod
    def filter_todos(
        user_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Todo]:
        """Filter todos by various criteria.
        
        Args:
            user_id: The user's UUID
            status: Filter by status (all, active, completed)
            priority: Filter by priority level
            search: Search term for title/description
            
        Returns:
            List of matching todos
        """
        query = Todo.query.filter_by(user_id=user_id)
        
        if status == 'active':
            query = query.filter_by(is_completed=False)
        elif status == 'completed':
            query = query.filter_by(is_completed=True)
        
        if priority:
            query = query.filter_by(priority=priority)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Todo.title.ilike(search_term),
                    Todo.description.ilike(search_term)
                )
            )
        
        return query.all()
    
    @staticmethod
    def bulk_delete_todos(user_id: str, todo_ids: List[str]) -> int:
        """Delete multiple todos by ID.
        
        Args:
            user_id: The user's UUID for ownership verification
            todo_ids: List of todo IDs to delete
            
        Returns:
            Number of todos deleted
        """
        result = Todo.query.filter(
            Todo.id.in_(todo_ids),
            Todo.user_id == user_id
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return result
    
    @staticmethod
    def get_todo_stats(user_id: str) -> dict:
        """Get todo statistics for a user.
        
        Args:
            user_id: The user's UUID
            
        Returns:
            Dictionary with statistics
        """
        # Get counts
        total = Todo.query.filter_by(user_id=user_id).count()
        completed = Todo.query.filter_by(user_id=user_id, is_completed=True).count()
        pending = total - completed
        
        # Calculate completion rate
        completion_rate = (completed / total * 100) if total > 0 else 0.0
        
        # Get counts by priority
        by_priority = {}
        for priority in PriorityLevel:
            count = Todo.query.filter_by(
                user_id=user_id,
                priority=priority.value
            ).count()
            by_priority[priority.value] = count
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'completion_rate': round(completion_rate, 2),
            'by_priority': by_priority
        }
    
    @staticmethod
    def mark_complete(todo: Todo) -> Todo:
        """Mark a todo as completed.
        
        Args:
            todo: The Todo to mark complete
            
        Returns:
            The updated Todo
        """
        todo.mark_complete()
        todo.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return todo
    
    @staticmethod
    def mark_incomplete(todo: Todo) -> Todo:
        """Mark a todo as not completed.
        
        Args:
            todo: The Todo to mark incomplete
            
        Returns:
            The updated Todo
        """
        todo.mark_incomplete()
        todo.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return todo
    
    @staticmethod
    def clear_completed(user_id: str) -> int:
        """Delete all completed todos for a user.
        
        Args:
            user_id: The user's UUID
            
        Returns:
            Number of todos deleted
        """
        result = Todo.query.filter_by(
            user_id=user_id,
            is_completed=True
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return result
    
    @staticmethod
    def bulk_update_todos(
        user_id: str,
        todo_ids: List[str],
        is_completed: Optional[bool] = None,
        priority: Optional[PriorityLevel] = None
    ) -> int:
        """Update multiple todos.
        
        Args:
            user_id: The user's UUID
            todo_ids: List of todo IDs to update
            is_completed: New completion status
            priority: New priority level
            
        Returns:
            Number of todos updated
        """
        todos = Todo.query.filter(
            Todo.id.in_(todo_ids),
            Todo.user_id == user_id
        ).all()
        
        updated_count = 0
        for todo in todos:
            if is_completed is not None:
                if is_completed and not todo.is_completed:
                    todo.mark_complete()
                elif not is_completed and todo.is_completed:
                    todo.mark_incomplete()
            
            if priority is not None:
                todo.priority = priority.value
            
            todo.updated_at = datetime.now(timezone.utc)
            updated_count += 1
        
        db.session.commit()
        return updated_count
