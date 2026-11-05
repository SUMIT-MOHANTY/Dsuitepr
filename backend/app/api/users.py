"""User API endpoints for user profile management."""

from flask import Blueprint, jsonify, request, g
from flask_login import login_required

from backend.app.extensions import db
from backend.app.models import User
from backend.app.schemas import UserResponse, UserUpdate
from backend.app.utils.decorators import csrf_protect, strict_rate_limit

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user profile.
    
    Returns:
        200: Current user data
        401: Not authenticated
    """
    response_data = UserResponse.model_validate(g.current_user)
    
    return jsonify({
        'success': True,
        'data': response_data.model_dump(),
        'message': 'User profile retrieved successfully'
    }), 200


@users_bp.route('/me', methods=['PUT'])
@login_required
@csrf_protect
@strict_rate_limit
def update_current_user():
    """Update current authenticated user profile.
    
    Request Body:
        - username: New username (optional, 3-30 chars, alphanumeric)
        - email: New email address (optional, valid email format)
    
    Returns:
        200: Updated user data
        400: Validation error
        401: Not authenticated
        409: Username or email already exists
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
        update_data = UserUpdate(**data)
        
        # Check for username conflicts
        if update_data.username and update_data.username != g.current_user.username:
            existing = User.query.filter_by(username=update_data.username).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'CONFLICT',
                        'message': 'Username already taken'
                    }
                }), 409
            g.current_user.username = update_data.username
        
        # Check for email conflicts
        if update_data.email and update_data.email != g.current_user.email:
            existing = User.query.filter_by(email=update_data.email).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'CONFLICT',
                        'message': 'Email already registered'
                    }
                }), 409
            g.current_user.email = update_data.email
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': UserResponse.model_validate(g.current_user).model_dump(),
            'message': 'Profile updated successfully'
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


@users_bp.route('/me', methods=['PATCH'])
@login_required
@csrf_protect
@strict_rate_limit
def patch_current_user():
    """Partially update current authenticated user profile.
    
    Request Body:
        - username: New username (optional, 3-30 chars, alphanumeric)
        - email: New email address (optional, valid email format)
    
    Returns:
        200: Updated user data
        400: Validation error
        401: Not authenticated
        409: Username or email already exists
    """
    # PATCH uses same logic as PUT since UserUpdate has optional fields
    return update_current_user()


@users_bp.route('/me', methods=['DELETE'])
@login_required
@csrf_protect
@strict_rate_limit
def delete_current_user():
    """Delete current authenticated user account.
    
    This permanently deletes the user account and all associated todos.
    
    Returns:
        200: Account deleted successfully
        401: Not authenticated
        500: Server error
    """
    try:
        user = g.current_user
        
        # Delete user (cascade will handle todos)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully'
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


@users_bp.route('/<string:user_id>', methods=['GET'])
@login_required
def get_user_by_id(user_id: str):
    """Get user profile by ID.
    
    Args:
        user_id: The user's UUID
    
    Returns:
        200: User data (limited public profile)
        401: Not authenticated
        404: User not found
    """
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'User not found'
            }
        }), 404
    
    # Return limited public profile for other users
    if user_id == g.current_user.id:
        response_data = UserResponse.model_validate(user)
    else:
        # For other users, return limited info
        response_data = {
            'id': user.id,
            'username': user.username,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    
    return jsonify({
        'success': True,
        'data': response_data.model_dump() if hasattr(response_data, 'model_dump') else response_data,
        'message': 'User profile retrieved successfully'
    }), 200


@users_bp.route('/<string:user_id>', methods=['PUT'])
@login_required
@csrf_protect
@strict_rate_limit
def update_user_by_id(user_id: str):
    """Update user profile by ID (admin or self only).
    
    Args:
        user_id: The user's UUID
    
    Request Body:
        - username: New username (optional, 3-30 chars, alphanumeric)
        - email: New email address (optional, valid email format)
    
    Returns:
        200: Updated user data
        400: Validation error
        401: Not authenticated
        403: Forbidden (not authorized)
        404: User not found
        409: Username or email already exists
    """
    # Only allow users to update their own profile
    if user_id != g.current_user.id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Not authorized to update this user'
            }
        }), 403
    
    # Delegate to update_current_user
    return update_current_user()


@users_bp.route('/<string:user_id>', methods=['DELETE'])
@login_required
@csrf_protect
@strict_rate_limit
def delete_user_by_id(user_id: str):
    """Delete user account by ID (admin or self only).
    
    Args:
        user_id: The user's UUID
    
    Returns:
        200: Account deleted successfully
        401: Not authenticated
        403: Forbidden (not authorized)
        404: User not found
    """
    # Only allow users to delete their own account
    if user_id != g.current_user.id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Not authorized to delete this user'
            }
        }), 403
    
    # Delegate to delete_current_user
    return delete_current_user()
