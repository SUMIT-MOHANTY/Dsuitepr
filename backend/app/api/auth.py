"""Authentication API endpoints for user registration and login."""

from flask import Blueprint, request, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError

from backend.app.extensions import db
from backend.app.models import User
from backend.app.schemas import UserCreate, UserLogin, UserResponse
from backend.app.utils.decorators import (
    csrf_protect, 
    auth_rate_limit, 
    set_csrf_cookie,
    generate_csrf_token
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Generate and return a CSRF token.
    
    Returns:
        200: CSRF token in response body and set as cookie.
        The token must be included in the X-CSRF-Token header
        for all state-changing requests (POST, PUT, PATCH, DELETE).
    """
    token = generate_csrf_token()
    
    response = make_response(jsonify({
        'success': True,
        'data': {
            'csrf_token': token
        },
        'message': 'CSRF token generated'
    }))
    
    # Set CSRF token in cookie for double-submit pattern
    set_csrf_cookie(response)
    
    return response, 200


@auth_bp.route('/register', methods=['POST'])
@auth_rate_limit
def register():
    """Register a new user.
    
    Request Body:
        - username: str (required, unique, 3-80 chars)
        - email: str (required, unique, valid email)
        - password: str (required, min 8 chars)
        
    Returns:
        201: User created successfully with user data
        400: Validation error or missing fields
        409: Username or email already exists
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Request body is required'
            }
        }), 400
    
    # Validate input using Pydantic schema
    try:
        user_data = UserCreate(**data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': str(e)
            }
        }), 400
    
    # Check if username already exists
    if User.query.filter_by(username=user_data.username).first():
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': 'Username already exists'
            }
        }), 409
    
    # Check if email already exists
    if User.query.filter_by(email=user_data.email).first():
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': 'Email already exists'
            }
        }), 409
    
    # Create new user
    try:
        user = User(
            username=user_data.username,
            email=user_data.email
        )
        user.set_password(user_data.password)
        
        db.session.add(user)
        db.session.commit()
        
        # Return user response
        response_data = UserResponse.model_validate(user)
        
        return jsonify({
            'success': True,
            'data': response_data.model_dump(),
            'message': 'User registered successfully'
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONFLICT',
                'message': 'Username or email already exists'
            }
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to create user',
                'details': str(e)
            }
        }), 500


@auth_bp.route('/login', methods=['POST'])
@auth_rate_limit
def login():
    """Authenticate user and create session.
    
    Request Body:
        - username: str (required)
        - password: str (required)
        
    Returns:
        200: Login successful with user data
        400: Missing fields
        401: Invalid credentials
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Request body is required'
            }
        }), 400
    
    # Validate input using Pydantic schema
    try:
        login_data = UserLogin(**data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': str(e)
            }
        }), 400
    
    # Find user by username
    user = User.query.filter_by(username=login_data.username).first()
    
    # Verify user exists and password is correct
    if not user or not user.check_password(login_data.password):
        return jsonify({
            'success': False,
            'error': {
                'code': 'AUTHENTICATION_ERROR',
                'message': 'Invalid username or password'
            }
        }), 401
    
    # Check if user is active
    if not user.is_active:
        return jsonify({
            'success': False,
            'error': {
                'code': 'AUTHENTICATION_ERROR',
                'message': 'Account is deactivated'
            }
        }), 401
    
    # Create session
    login_user(user, remember=True)
    
    # Return user response
    response_data = UserResponse.model_validate(user)
    
    response = make_response(jsonify({
        'success': True,
        'data': response_data.model_dump(),
        'message': 'Login successful'
    }))
    
    # Set CSRF token for subsequent requests
    set_csrf_cookie(response)
    
    return response, 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
@csrf_protect
def logout():
    """End user session.
    
    Returns:
        200: Logout successful
        401: Not authenticated
    """
    logout_user()
    
    return jsonify({
        'success': True,
        'data': None,
        'message': 'Logout successful'
    }), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user.
    
    Returns:
        200: Current user data
        401: Not authenticated
    """
    response_data = UserResponse.model_validate(current_user)
    
    return jsonify({
        'success': True,
        'data': response_data.model_dump(),
        'message': 'Current user retrieved successfully'
    }), 200
