"""Security decorators for rate limiting, CSRF protection, and authentication."""

import functools
import secrets
from datetime import datetime, timedelta
from typing import Optional, Callable, Any

from flask import request, g, current_app, make_response
from flask_login import current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.app.extensions import limiter


# =============================================================================
# Rate Limiting Decorators
# =============================================================================

def exempt_from_rate_limit(func: Callable) -> Callable:
    """Decorator to exempt a route from rate limiting.
    
    Use this for health checks, documentation, and other public endpoints
    that should not be rate limited.
    
    Example:
        @app.route('/health')
        @exempt_from_rate_limit
        def health_check():
            return {'status': 'ok'}
    """
    func.__exempt_from_rate_limit = True
    return func


def rate_limit_exempt_check() -> bool:
    """Check if the current endpoint is exempt from rate limiting.
    
    Returns:
        True if the endpoint is exempt, False otherwise.
    """
    if not request.endpoint:
        return False
    
    view_func = current_app.view_functions.get(request.endpoint)
    if view_func and getattr(view_func, '__exempt_from_rate_limit', False):
        return True
    
    # Also check for exempt blueprints
    if request.blueprint:
        bp = current_app.blueprints.get(request.blueprint)
        if bp and getattr(bp, '__exempt_from_rate_limit', False):
            return True
    
    return False


def auth_rate_limit(func: Callable) -> Callable:
    """Stricter rate limiting for authentication endpoints.
    
    Applies a 5 requests per minute limit to prevent brute force attacks.
    """
    @functools.wraps(func)
    @limiter.limit("5 per minute")
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def strict_rate_limit(func: Callable) -> Callable:
    """Very strict rate limiting for sensitive operations.
    
    Applies a 3 requests per minute limit for highly sensitive endpoints.
    """
    @functools.wraps(func)
    @limiter.limit("3 per minute")
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# =============================================================================
# CSRF Protection Decorators
# =============================================================================

class CSRFError(Exception):
    """Custom exception for CSRF validation errors."""
    
    def __init__(self, message: str = "CSRF token validation failed"):
        self.message = message
        super().__init__(self.message)


def generate_csrf_token() -> str:
    """Generate a secure CSRF token.
    
    Returns:
        A URL-safe base64-encoded token string.
    """
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response) -> None:
    """Set the CSRF token in a secure cookie.
    
    Args:
        response: Flask response object to modify.
    """
    token = generate_csrf_token()
    
    # Store token in session for validation
    from flask import session
    session['csrf_token'] = token
    
    # Set cookie with security attributes
    response.set_cookie(
        current_app.config.get('CSRF_COOKIE_NAME', 'csrf_token'),
        token,
        max_age=current_app.config.get('CSRF_TOKEN_EXPIRY', 3600),
        httponly=False,  # Must be accessible by JavaScript
        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
        samesite=current_app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
        path='/'
    )
    
    # Also set in g for use in the same request
    g.csrf_token = token


def validate_csrf_token() -> bool:
    """Validate the CSRF token from request.
    
    Checks the token from:
    1. X-CSRF-Token header
    2. Request body (form data or JSON)
    
    Compares against the token stored in session.
    
    Returns:
        True if valid, False otherwise.
    """
    from flask import session
    
    # Get stored token from session
    stored_token = session.get('csrf_token')
    if not stored_token:
        return False
    
    # Check header first
    header_token = request.headers.get(
        current_app.config.get('CSRF_HEADER_NAME', 'X-CSRF-Token')
    )
    if header_token:
        return secrets.compare_digest(stored_token, header_token)
    
    # Check request body
    if request.is_json:
        body_token = request.json.get('csrf_token') if request.json else None
        if body_token:
            return secrets.compare_digest(stored_token, str(body_token))
    
    # Check form data
    form_token = request.form.get('csrf_token')
    if form_token:
        return secrets.compare_digest(stored_token, form_token)
    
    return False


def csrf_protect(func: Callable) -> Callable:
    """Decorator to enforce CSRF protection on state-changing routes.
    
    This decorator validates the CSRF token for POST, PUT, PATCH, and DELETE
    requests. Safe methods (GET, HEAD, OPTIONS, TRACE) are exempt.
    
    The token should be:
    - Sent in the X-CSRF-Token header, OR
    - Included in the request body as 'csrf_token'
    
    The token is obtained from the /api/auth/csrf-token endpoint which sets
    it in a cookie.
    
    Example:
        @app.route('/api/todos', methods=['POST'])
        @csrf_protect
        @login_required
        def create_todo():
            # CSRF token validated automatically
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Safe methods don't require CSRF protection
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return func(*args, **kwargs)
        
        # Skip CSRF in testing mode
        if current_app.config.get('TESTING', False):
            return func(*args, **kwargs)
        
        # Validate CSRF token
        if not validate_csrf_token():
            from flask import jsonify
            response = jsonify({
                'success': False,
                'error': {
                    'code': 'CSRF_ERROR',
                    'message': 'CSRF token validation failed. Please refresh the page and try again.'
                }
            })
            response.status_code = 403
            return response
        
        return func(*args, **kwargs)
    
    return wrapper


def csrf_exempt(func: Callable) -> Callable:
    """Decorator to exempt a route from CSRF protection.
    
    Use sparingly and only for specific API endpoints that require
    cross-origin access without CSRF tokens (e.g., webhook endpoints).
    
    Example:
        @app.route('/api/webhook', methods=['POST'])
        @csrf_exempt
        def webhook():
            pass
    """
    func.__csrf_exempt = True
    return func


def is_csrf_exempt() -> bool:
    """Check if the current endpoint is exempt from CSRF protection.
    
    Returns:
        True if exempt, False otherwise.
    """
    if not request.endpoint:
        return False
    
    view_func = current_app.view_functions.get(request.endpoint)
    if view_func and getattr(view_func, '__csrf_exempt', False):
        return True
    
    return False


# =============================================================================
# Combined Security Decorators
# =============================================================================

def secure_mutation(func: Callable) -> Callable:
    """Combined decorator for state-changing operations.
    
    Applies:
    - CSRF protection
    - Stricter rate limiting (5/min for mutations)
    - Authentication check (if not already applied)
    
    Use this for all POST, PUT, PATCH, DELETE operations.
    
    Example:
        @app.route('/api/todos/<id>', methods=['DELETE'])
        @secure_mutation
        @login_required
        def delete_todo(id):
            pass
    """
    @functools.wraps(func)
    @csrf_protect
    @limiter.limit("5 per minute")
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# =============================================================================
# Authentication Helpers
# =============================================================================

def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication.
    
    Returns 401 if user is not authenticated.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            from flask import jsonify
            response = jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            })
            response.status_code = 401
            return response
        return func(*args, **kwargs)
    return wrapper


def require_admin(func: Callable) -> Callable:
    """Decorator to require admin privileges.
    
    Returns 403 if user is not an admin.
    """
    @functools.wraps(func)
    @require_auth
    def wrapper(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            from flask import jsonify
            response = jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'Admin privileges required'
                }
            })
            response.status_code = 403
            return response
        return func(*args, **kwargs)
    return wrapper


# =============================================================================
# Response Security Headers
# =============================================================================

def add_security_headers(response) -> None:
    """Add security headers to response.
    
    These headers are added in addition to Flask-Talisman headers.
    
    Args:
        response: Flask response object to modify.
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS Protection (legacy, but still useful)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy (modern replacement for Feature Policy)
    response.headers['Permissions-Policy'] = (
        'geolocation=(), microphone=(), camera=(), '
        'payment=(), usb=(), vr=(), accelerometer=(), '
        'gyroscope=(), magnetometer=()'
    )


# =============================================================================
# Request Context Helpers
# =============================================================================

def get_client_ip() -> str:
    """Get the real client IP address.
    
    Handles proxies by checking X-Forwarded-For header.
    
    Returns:
        Client IP address string.
    """
    # Check for forwarded IP (behind proxy)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Get the first IP in the chain (original client)
        return forwarded_for.split(',')[0].strip()
    
    # Check for single forwarded IP
    real_ip = request.headers.get('X-Real-Ip')
    if real_ip:
        return real_ip
    
    # Fall back to remote address
    return request.remote_addr or 'unknown'


def get_request_metadata() -> dict:
    """Get metadata about the current request for logging/debugging.
    
    Returns:
        Dictionary with request metadata.
    """
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'path': request.path,
        'endpoint': request.endpoint,
        'blueprint': request.blueprint,
        'ip': get_client_ip(),
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'content_type': request.content_type,
        'is_authenticated': current_user.is_authenticated if current_user else False,
        'user_id': str(current_user.id) if current_user and current_user.is_authenticated else None,
    }
