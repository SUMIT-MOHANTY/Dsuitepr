"""API blueprint registration and application factory helpers."""

from flask import Blueprint, jsonify, request, g
from flask_login import login_required, current_user

from backend.app.api.auth import auth_bp
from backend.app.api.todos import todos_bp
from backend.app.api.users import users_bp
from backend.app.extensions import cors, talisman, limiter
from backend.app.utils.decorators import (
    exempt_from_rate_limit,
    set_csrf_cookie,
    add_security_headers
)


def register_api_blueprints(app):
    """Register all API blueprints with the Flask application.
    
    This function sets up:
    - CORS configuration for cross-origin requests
    - Rate limiting with exemptions for health/docs endpoints
    - Security headers via Flask-Talisman
    - CSRF token handling
    - API blueprints for auth, todos, and users
    
    Args:
        app: Flask application instance
    """
    # =======================================================================
    # CORS Configuration
    # =======================================================================
    # CORS is initialized in extensions.py, but we configure it here
    # based on the environment-specific settings
    cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:5173'])
    
    # =======================================================================
    # Security Headers via Flask-Talisman
    # =======================================================================
    # Talisman is initialized in extensions.py with default security headers
    # Additional headers are added via after_request handler
    
    @app.after_request
    def after_request(response):
        """Add security headers and CSRF cookie after each request."""
        # Add additional security headers
        add_security_headers(response)
        
        # Set CSRF cookie for GET requests (so token is available for mutations)
        if request.method == 'GET' and not request.endpoint == 'static':
            set_csrf_cookie(response)
        
        return response
    
    # =======================================================================
    # Rate Limit Error Handler
    # =======================================================================
    @app.errorhandler(429)
    def rate_limit_handler(e):
        """Handle rate limit exceeded errors."""
        return jsonify({
            'success': False,
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Rate limit exceeded. Please try again later.',
                'details': {
                    'retry_after': getattr(e, 'retry_after', 60)
                }
            }
        }), 429
    
    # =======================================================================
    # CSRF Error Handler
    # =======================================================================
    @app.errorhandler(403)
    def csrf_error_handler(e):
        """Handle CSRF validation errors."""
        if 'CSRF' in str(e.description).upper():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'CSRF_ERROR',
                    'message': 'CSRF token validation failed. Please refresh the page and try again.',
                    'details': {}
                }
            }), 403
        # Re-raise for other 403 errors
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': str(e.description) if hasattr(e, 'description') else 'Access forbidden'
            }
        }), 403
    
    # =======================================================================
    # Blueprint Registration
    # =======================================================================
    
    # Register authentication blueprint
    # Auth endpoints have stricter rate limits applied in auth.py
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Register todos blueprint
    # Todo mutation endpoints have CSRF protection and stricter rate limits
    app.register_blueprint(todos_bp, url_prefix='/api/todos')
    
    # Register users blueprint
    # User mutation endpoints have CSRF protection and stricter rate limits
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # =======================================================================
    # Health Check Endpoint (Rate Limit Exempt)
    # =======================================================================
    @app.route('/health', methods=['GET'])
    @exempt_from_rate_limit
    def health_check():
        """Health check endpoint.
        
        Exempt from rate limiting to allow monitoring systems
        to poll without restrictions.
        
        Returns:
            200: Service is healthy
        """
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'flask-react-todo-api',
                'version': '1.0.0',
                'timestamp': g.get('request_metadata', {}).get('timestamp') if hasattr(g, 'request_metadata') else None
            },
            'message': 'Service is healthy'
        }), 200
    
    # =======================================================================
    # API Documentation Endpoint (Rate Limit Exempt)
    # =======================================================================
    @app.route('/api/docs', methods=['GET'])
    @exempt_from_rate_limit
    def api_docs():
        """API documentation endpoint.
        
        Exempt from rate limiting to allow developers to access
        documentation without restrictions.
        
        Returns:
            200: API documentation and available endpoints
        """
        return jsonify({
            'success': True,
            'data': {
                'name': 'Flask React Todo API',
                'version': '1.0.0',
                'description': 'A secure REST API for personal task management',
                'security': {
                    'authentication': 'Session-based with Flask-Login',
                    'csrf_protection': 'Required for state-changing operations',
                    'rate_limiting': '100 requests/minute default, 5/minute for auth/mutations'
                },
                'endpoints': {
                    'health': {
                        'path': '/health',
                        'method': 'GET',
                        'description': 'Service health check'
                    },
                    'docs': {
                        'path': '/api/docs',
                        'method': 'GET',
                        'description': 'This documentation'
                    },
                    'auth': {
                        'register': {
                            'path': '/api/auth/register',
                            'method': 'POST',
                            'description': 'Register new user',
                            'rate_limit': '5/minute'
                        },
                        'login': {
                            'path': '/api/auth/login',
                            'method': 'POST',
                            'description': 'Authenticate user',
                            'rate_limit': '5/minute'
                        },
                        'logout': {
                            'path': '/api/auth/logout',
                            'method': 'POST',
                            'description': 'End session',
                            'csrf_required': True
                        },
                        'me': {
                            'path': '/api/auth/me',
                            'method': 'GET',
                            'description': 'Get current user info'
                        },
                        'csrf_token': {
                            'path': '/api/auth/csrf-token',
                            'method': 'GET',
                            'description': 'Get CSRF token for mutations'
                        }
                    },
                    'users': {
                        'me': {
                            'path': '/api/users/me',
                            'method': 'GET',
                            'description': 'Get current user profile'
                        },
                        'update': {
                            'path': '/api/users/{id}',
                            'method': 'PUT',
                            'description': 'Update user profile',
                            'csrf_required': True,
                            'rate_limit': '5/minute'
                        },
                        'delete': {
                            'path': '/api/users/{id}',
                            'method': 'DELETE',
                            'description': 'Delete user account',
                            'csrf_required': True,
                            'rate_limit': '3/minute'
                        }
                    },
                    'todos': {
                        'list': {
                            'path': '/api/todos',
                            'method': 'GET',
                            'description': 'List todos with filtering and pagination'
                        },
                        'create': {
                            'path': '/api/todos',
                            'method': 'POST',
                            'description': 'Create new todo',
                            'csrf_required': True,
                            'rate_limit': '5/minute'
                        },
                        'get': {
                            'path': '/api/todos/{id}',
                            'method': 'GET',
                            'description': 'Get single todo'
                        },
                        'update': {
                            'path': '/api/todos/{id}',
                            'method': 'PUT',
                            'description': 'Full update of todo',
                            'csrf_required': True,
                            'rate_limit': '5/minute'
                        },
                        'patch': {
                            'path': '/api/todos/{id}',
                            'method': 'PATCH',
                            'description': 'Partial update of todo',
                            'csrf_required': True,
                            'rate_limit': '5/minute'
                        },
                        'delete': {
                            'path': '/api/todos/{id}',
                            'method': 'DELETE',
                            'description': 'Delete todo',
                            'csrf_required': True,
                            'rate_limit': '5/minute'
                        },
                        'complete': {
                            'path': '/api/todos/{id}/complete',
                            'method': 'PATCH',
                            'description': 'Mark todo as complete',
                            'csrf_required': True,
                            'rate_limit': '5/minute'
                        },
                        'incomplete': {
                            'path': '/api/todos/{id}/incomplete',
                            'method': 'PATCH',
                            'description': 'Mark todo as incomplete',
                            'csrf_required': True,
                            'rate_limit': '5/minute'
                        },
                        'stats': {
                            'path': '/api/todos/stats',
                            'method': 'GET',
                            'description': 'Get todo statistics'
                        },
                        'bulk': {
                            'path': '/api/todos/bulk',
                            'method': 'POST',
                            'description': 'Bulk operations on todos',
                            'csrf_required': True,
                            'rate_limit': '3/minute'
                        },
                        'clear_completed': {
                            'path': '/api/todos/completed',
                            'method': 'DELETE',
                            'description': 'Delete all completed todos',
                            'csrf_required': True,
                            'rate_limit': '3/minute'
                        }
                    }
                }
            },
            'message': 'API documentation retrieved successfully'
        }), 200
    
    # =======================================================================
    # API Info Endpoint (Rate Limit Exempt)
    # =======================================================================
    @app.route('/api', methods=['GET'])
    @exempt_from_rate_limit
    def api_info():
        """API information endpoint (deprecated, use /api/docs).
        
        Returns:
            200: API information and available endpoints
        """
        return jsonify({
            'success': True,
            'data': {
                'name': 'Flask React Todo API',
                'version': '1.0.0',
                'documentation': '/api/docs',
                'health': '/health'
            },
            'message': 'API is running. See /api/docs for full documentation.'
        }), 200
    
    # =======================================================================
    # Request Context Setup
    # =======================================================================
    @app.before_request
    def before_request():
        """Set up request context with metadata."""
        from backend.app.utils.decorators import get_request_metadata
        g.request_metadata = get_request_metadata()
