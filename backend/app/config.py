"""Flask application configuration classes."""

import os
from datetime import timedelta


class Config:
    """Base configuration class."""
    
    # Flask core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///app.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS - Environment-specific origins
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With', 'X-CSRF-Token']
    CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRF-Token']
    CORS_MAX_AGE = 86400  # 24 hours
    
    # Rate Limiting - Flask-Limiter configuration
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_STORAGE_OPTIONS = {}
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = '100 per minute'
    RATELIMIT_ENABLED = True
    RATELIMIT_HEADERS_ENABLED = True
    
    # Stricter rate limits for auth endpoints
    RATELIMIT_AUTH_DEFAULT = '5 per minute'
    
    # CSRF Protection
    CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY', SECRET_KEY)
    CSRF_TOKEN_EXPIRY = 3600  # 1 hour in seconds
    CSRF_COOKIE_NAME = 'csrf_token'
    CSRF_HEADER_NAME = 'X-CSRF-Token'
    
    # Security Headers (Flask-Talisman)
    SECURITY_HEADERS_ENABLED = True
    CSP_NONCE_SECRET = os.environ.get('CSP_NONCE_SECRET', SECRET_KEY)
    
    # Content Security Policy
    CSP_DEFAULT_SRC = ["'self'"]
    CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'"]
    CSP_STYLE_SRC = ["'self'", "'unsafe-inline'"]
    CSP_IMG_SRC = ["'self'", "data:", "https:"]
    CSP_FONT_SRC = ["'self'", "data:"]
    CSP_CONNECT_SRC = ["'self'"]
    
    # Feature Policy / Permissions Policy
    FEATURE_POLICY = {
        'geolocation': "'none'",
        'microphone': "'none'",
        'camera': "'none'",
        'payment': "'none'",
        'usb': "'none'",
        'vr': "'none'",
    }
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Input Validation
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # More permissive CORS for development - includes Vite default port
    CORS_ORIGINS = [
        'http://localhost:3000', 
        'http://127.0.0.1:3000',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:8080',
    ]
    
    # Update CSP connect-src for development
    CSP_CONNECT_SRC = ["'self'"] + CORS_ORIGINS
    
    # SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///dev.db'
    )
    
    # Disable some security headers in development for easier debugging
    SECURITY_HEADERS_ENABLED = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Security headers - strict mode
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    SECURITY_HEADERS_ENABLED = True
    
    # Stricter rate limiting in production
    RATELIMIT_DEFAULT = '60 per minute'
    RATELIMIT_AUTH_DEFAULT = '3 per minute'
    
    # Production CORS - must be explicitly configured
    CORS_ORIGINS = os.environ.get(
        'CORS_ORIGINS', 
        'https://yourdomain.com'
    ).split(',')
    
    # Update CSP connect-src for production
    CSP_CONNECT_SRC = ["'self'"] + CORS_ORIGINS
    
    # HSTS settings
    HSTS_MAX_AGE = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS = True
    HSTS_PRELOAD = True
    
    # Frame options
    FRAME_OPTIONS = 'DENY'
    
    # Referrer policy
    REFERRER_POLICY = 'strict-origin-when-cross-origin'


class TestingConfig(Config):
    """Testing configuration."""
    
    DEBUG = True
    TESTING = True
    
    # In-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    CSRF_TOKEN_EXPIRY = 3600
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = 'memory://'
    
    # Disable security headers for testing
    SECURITY_HEADERS_ENABLED = False
    
    # Permissive CORS for testing
    CORS_ORIGINS = ['*']
    
    # Fast bcrypt rounds for testing
    BCRYPT_LOG_ROUNDS = 4


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)


def get_cors_origins():
    """Get CORS origins as a list from environment or config."""
    origins = os.environ.get('CORS_ORIGINS')
    if origins:
        return origins.split(',')
    return DevelopmentConfig.CORS_ORIGINS


def get_rate_limit_config():
    """Get rate limiting configuration dictionary."""
    return {
        'storage_uri': os.environ.get('REDIS_URL', 'memory://'),
        'strategy': 'fixed-window',
        'default_limits': ['100 per minute'],
        'enabled': os.environ.get('RATELIMIT_ENABLED', 'true').lower() == 'true',
    }
