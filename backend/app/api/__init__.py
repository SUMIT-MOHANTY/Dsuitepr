"""API blueprint registration and application factory helpers."""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from backend.app.api.auth import auth_bp
from backend.app.api.todos import todos_bp
from backend.app.api.users import users_bp


def register_api_blueprints(app):
    """Register all API blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register authentication blueprint
    app.register_blueprint(auth_bp)
    
    # Register todos blueprint
    app.register_blueprint(todos_bp)
    
    # Register users blueprint
    app.register_blueprint(users_bp)
    
    # Register health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint.
        
        Returns:
            200: Service is healthy
        """
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'flask-react-todo-api',
                'version': '1.0.0'
            },
            'message': 'Service is healthy'
        }), 200
    
    # Register API info endpoint
    @app.route('/api', methods=['GET'])
    def api_info():
        """API information endpoint.
        
        Returns:
            200: API information and available endpoints
        """
        return jsonify({
            'success': True,
            'data': {
                'name': 'Flask React Todo API',
                'version': '1.0.0',
                'endpoints': {
                    'health': '/health',
                    'auth': {
                        'register': 'POST /api/auth/register',
                        'login': 'POST /api/auth/login',
                        'logout': 'POST /api/auth/logout',
                        'me': 'GET /api/auth/me'
                    },
                    'users': {
                        'me': 'GET /api/users/me'
                    },
                    'todos': {
                        'list': 'GET /api/todos',
                        'create': 'POST /api/todos',
                        'get': 'GET /api/todos/{id}',
                        'update': 'PUT /api/todos/{id}',
                        'patch': 'PATCH /api/todos/{id}',
                        'delete': 'DELETE /api/todos/{id}',
                        'complete': 'PATCH /api/todos/{id}/complete',
                        'incomplete': 'PATCH /api/todos/{id}/incomplete',
                        'stats': 'GET /api/todos/stats',
                        'bulk': 'POST /api/todos/bulk',
                        'clear_completed': 'DELETE /api/todos/completed'
                    }
                }
            },
            'message': 'API information retrieved successfully'
        }), 200
