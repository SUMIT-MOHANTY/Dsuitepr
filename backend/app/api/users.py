"""User API endpoints for user profile management."""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from backend.app.schemas import UserResponse

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user profile.
    
    Returns:
        200: Current user data
        401: Not authenticated
    """
    response_data = UserResponse.model_validate(current_user)
    
    return jsonify({
        'success': True,
        'data': response_data.model_dump(),
        'message': 'User profile retrieved successfully'
    }), 200
