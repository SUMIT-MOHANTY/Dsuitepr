"""Todo API endpoints for CRUD operations."""

from datetime import datetime, timezone
from typing import Tuple

from flask import Blueprint, request, jsonify, g
from sqlalchemy import or_, and_

from backend.app.extensions import db
from backend.app.models import Todo, User
from backend.app.models.todo import PriorityLevel
from backend.app.schemas import (
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoListResponse,
    TodoStats,
    TodoBulkUpdate,
    TodoBulkDelete,
    TodoFilterParams,
)
from backend.app.api.auth import login_required

# Create blueprint
todos_bp = Blueprint('todos', __name__, url_prefix='/api/todos')


def get_pagination_params() -> Tuple[int, int]:
    """Extract pagination parameters from request query string.
    
    Returns:
        Tuple of (page, per_page) with validated defaults
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Validate bounds
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    
    return page, per_page


def build_todo_query(user_id: str, filter_params: TodoFilterParams):
    """Build filtered and sorted todo query.
    
    Args:
        user_id: The user's ID to filter by
        filter_params: Filter and sort parameters
        
    Returns:
        SQLAlchemy query object
    """
    query = Todo.query.filter_by(user_id=user_id)
    
    # Apply status filter
    if filter_params.status:
        if filter_params.status == 'active':
            query = query.filter_by(is_completed=False)
        elif filter_params.status == 'completed':
            query = query.filter_by(is_completed=True)
    
    # Apply priority filter
    if filter_params.priority:
        query = query.filter_by(priority=filter_params.priority.value)
    
    # Apply search filter
    if filter_params.search:
        search_term = f"%{filter_params.search}%"
        query = query.filter(
            or_(
                Todo.title.ilike(search_term),
                Todo.description.ilike(search_term)
            )
        )
    
    # Apply sorting
    sort_column = getattr(Todo, filter_params.sort_by, Todo.created_at)
    if filter_params.sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    return query


@todos_bp.route('', methods=['GET'])
@login_required
def get_todos():
    """Get all todos for the current user with filtering and pagination.
    
    Query Parameters:
        - status: Filter by status (all, active, completed)
        - priority: Filter by priority (low, medium, high)
        - search: Search in title and description
        - sort_by: Sort field (created_at, updated_at, due_date, priority, title)
        - sort_order: Sort order (asc, desc)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 100)
    
    Returns:
        JSON response with paginated todo list
    """
    try:
        # Parse filter parameters
        filter_data = {
            'status': request.args.get('status'),
            'priority': request.args.get('priority'),
            'search': request.args.get('search'),
            'sort_by': request.args.get('sort_by', 'created_at'),
            'sort_order': request.args.get('sort_order', 'desc'),
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 50, type=int),
        }
        
        # Remove None values
        filter_data = {k: v for k, v in filter_data.items() if v is not None}
        
        filter_params = TodoFilterParams(**filter_data)
        page, per_page = get_pagination_params()
        
        # Build and execute query
        query = build_todo_query(g.current_user.id, filter_params)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Build response
        todos_data = [TodoResponse.model_validate(todo).model_dump() for todo in pagination.items]
        
        response = TodoListResponse(
            items=todos_data,
            total=pagination.total,
            page=page,
            per_page=per_page,
            pages=pagination.pages
        )
        
        return jsonify({
            'success': True,
            'data': response.model_dump()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FILTER_ERROR',
                'message': str(e)
            }
        }), 400


@todos_bp.route('', methods=['POST'])
@login_required
def create_todo():
    """Create a new todo item.
    
    Request Body:
        - title: Todo title (required, 1-200 chars)
        - description: Optional description (max 2000 chars)
        - priority: Priority level (low, medium, high), default: medium
        - due_date: Optional due date (ISO 8601 format)
    
    Returns:
        JSON response with created todo data
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Validate input
        todo_data = TodoCreate(**data)
        
        # Create todo
        todo = Todo(
            user_id=g.current_user.id,
            title=todo_data.title,
            description=todo_data.description,
            priority=todo_data.priority.value,
            due_date=todo_data.due_date,
            is_completed=False
        )
        
        db.session.add(todo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': TodoResponse.model_validate(todo).model_dump(),
            'message': 'Todo created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


@todos_bp.route('/<string:todo_id>', methods=['GET'])
@login_required
def get_todo(todo_id: str):
    """Get a single todo by ID.
    
    Args:
        todo_id: The todo's UUID
    
    Returns:
        JSON response with todo data
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=g.current_user.id).first()
    
    if not todo:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Todo not found'
            }
        }), 404
    
    return jsonify({
        'success': True,
        'data': TodoResponse.model_validate(todo).model_dump()
    }), 200


@todos_bp.route('/<string:todo_id>', methods=['PUT'])
@login_required
def update_todo(todo_id: str):
    """Update a todo completely (all fields required).
    
    Args:
        todo_id: The todo's UUID
    
    Request Body:
        - title: Todo title (required)
        - description: Optional description
        - priority: Priority level
        - due_date: Optional due date
        - is_completed: Completion status
    
    Returns:
        JSON response with updated todo data
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=g.current_user.id).first()
    
    if not todo:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Todo not found'
            }
        }), 404
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Validate input
        update_data = TodoUpdate(**data)
        
        # Update fields
        if update_data.title is not None:
            todo.title = update_data.title
        if update_data.description is not None:
            todo.description = update_data.description
        if update_data.priority is not None:
            todo.priority = update_data.priority.value
        if update_data.due_date is not None:
            todo.due_date = update_data.due_date
        if update_data.is_completed is not None:
            if update_data.is_completed and not todo.is_completed:
                todo.mark_complete()
            elif not update_data.is_completed and todo.is_completed:
                todo.mark_incomplete()
        
        todo.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': TodoResponse.model_validate(todo).model_dump(),
            'message': 'Todo updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(e)
            }
        }), 400


@todos_bp.route('/<string:todo_id>', methods=['PATCH'])
@login_required
def patch_todo(todo_id: str):
    """Partially update a todo (fields optional).
    
    Args:
        todo_id: The todo's UUID
    
    Request Body:
        - title: Todo title (optional)
        - description: Description (optional)
        - priority: Priority level (optional)
        - due_date: Due date (optional)
        - is_completed: Completion status (optional)
    
    Returns:
        JSON response with updated todo data
    """
    # PATCH uses same logic as PUT since TodoUpdate has optional fields
    return update_todo(todo_id)


@todos_bp.route('/<string:todo_id>', methods=['DELETE'])
@login_required
def delete_todo(todo_id: str):
    """Delete a todo.
    
    Args:
        todo_id: The todo's UUID
    
    Returns:
        JSON response confirming deletion
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=g.current_user.id).first()
    
    if not todo:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Todo not found'
            }
        }), 404
    
    try:
        db.session.delete(todo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todo deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'DELETE_ERROR',
                'message': str(e)
            }
        }), 500


@todos_bp.route('/<string:todo_id>/complete', methods=['PATCH'])
@login_required
def mark_complete(todo_id: str):
    """Mark a todo as completed.
    
    Args:
        todo_id: The todo's UUID
    
    Returns:
        JSON response with updated todo data
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=g.current_user.id).first()
    
    if not todo:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Todo not found'
            }
        }), 404
    
    try:
        todo.mark_complete()
        todo.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': TodoResponse.model_validate(todo).model_dump(),
            'message': 'Todo marked as complete'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'UPDATE_ERROR',
                'message': str(e)
            }
        }), 500


@todos_bp.route('/<string:todo_id>/incomplete', methods=['PATCH'])
@login_required
def mark_incomplete(todo_id: str):
    """Mark a todo as not completed.
    
    Args:
        todo_id: The todo's UUID
    
    Returns:
        JSON response with updated todo data
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=g.current_user.id).first()
    
    if not todo:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Todo not found'
            }
        }), 404
    
    try:
        todo.mark_incomplete()
        todo.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': TodoResponse.model_validate(todo).model_dump(),
            'message': 'Todo marked as incomplete'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'UPDATE_ERROR',
                'message': str(e)
            }
        }), 500


@todos_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get todo statistics for the current user.
    
    Returns:
        JSON response with completion statistics
    """
    user_id = g.current_user.id
    
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
    
    stats = TodoStats(
        total=total,
        completed=completed,
        pending=pending,
        completion_rate=round(completion_rate, 2),
        by_priority=by_priority
    )
    
    return jsonify({
        'success': True,
        'data': stats.model_dump()
    }), 200


@todos_bp.route('/bulk', methods=['POST'])
@login_required
def bulk_update():
    """Perform bulk operations on todos.
    
    Request Body:
        - ids: List of todo IDs to update (required)
        - is_completed: New completion status (optional)
        - priority: New priority level (optional)
    
    Returns:
        JSON response with number of updated items
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Request body is required'
                }
            }), 400
        
        bulk_data = TodoBulkUpdate(**data)
        
        # Query todos belonging to current user
        todos = Todo.query.filter(
            Todo.id.in_(bulk_data.ids),
            Todo.user_id == g.current_user.id
        ).all()
        
        updated_count = 0
        for todo in todos:
            if bulk_data.is_completed is not None:
                if bulk_data.is_completed and not todo.is_completed:
                    todo.mark_complete()
                elif not bulk_data.is_completed and todo.is_completed:
                    todo.mark_incomplete()
            
            if bulk_data.priority is not None:
                todo.priority = bulk_data.priority.value
            
            todo.updated_at = datetime.now(timezone.utc)
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'updated_count': updated_count},
            'message': f'{updated_count} todos updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'BULK_UPDATE_ERROR',
                'message': str(e)
            }
        }), 400


@todos_bp.route('/completed', methods=['DELETE'])
@login_required
def clear_completed():
    """Delete all completed todos for the current user.
    
    Returns:
        JSON response with number of deleted items
    """
    try:
        result = Todo.query.filter_by(
            user_id=g.current_user.id,
            is_completed=True
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'deleted_count': result},
            'message': f'{result} completed todos deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'DELETE_ERROR',
                'message': str(e)
            }
        }), 500


@todos_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple todos by ID.
    
    Request Body:
        - ids: List of todo IDs to delete (required)
    
    Returns:
        JSON response with number of deleted items
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Request body is required'
                }
            }), 400
        
        bulk_data = TodoBulkDelete(**data)
        
        # Delete todos belonging to current user
        result = Todo.query.filter(
            Todo.id.in_(bulk_data.ids),
            Todo.user_id == g.current_user.id
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'deleted_count': result},
            'message': f'{result} todos deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'BULK_DELETE_ERROR',
                'message': str(e)
            }
        }), 400
