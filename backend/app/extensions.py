"""Flask extensions initialization."""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import secrets

# SQLAlchemy ORM instance
db = SQLAlchemy()

# Flask-Login instance
login_manager = LoginManager()

# Flask-CORS instance
cors = CORS()

# Flask-Limiter instance - initialized with storage fallback
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://",  # Will be overridden by config
    strategy="fixed-window"
)

# Flask-Talisman instance for security headers
talisman = Talisman()


def generate_csrf_token():
    """Generate a secure CSRF token."""
    return secrets.token_urlsafe(32)


@login_manager.user_loader
def load_user(user_id: str):
    """Load user by ID for Flask-Login.
    
    Args:
        user_id: The user's UUID as a string
        
    Returns:
        User instance or None if not found
    """
    from backend.app.models import User
    return User.query.get(user_id)


def init_extensions(app):
    """Initialize all Flask extensions with the app instance.
    
    Args:
        app: Flask application instance
    """
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this resource.'
    login_manager.login_message_category = 'info'
    
    # Initialize CORS with configuration from app config
    cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:5173', 'http://localhost:3000'])
    if isinstance(cors_origins, str):
        cors_origins = cors_origins.split(',')
    
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token"],
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "expose_headers": ["Content-Type", "X-CSRF-Token"],
                "max_age": 86400  # 24 hours
            }
        }
    )
    
    # Initialize Rate Limiter with storage from config
    storage_uri = app.config.get('RATELIMIT_STORAGE_URI', 'memory://')
    limiter.storage_uri = storage_uri
    limiter.init_app(app)
    
    # Initialize Talisman for security headers (only in production)
    if not app.config.get('DEBUG', False):
        talisman.init_app(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 year
            strict_transport_security_include_subdomains=True,
            content_security_policy={
                'default-src': "'self'",
                'script-src': ["'self'", "'unsafe-inline'"],
                'style-src': ["'self'", "'unsafe-inline'"],
                'img-src': ["'self'", "data:", "https:"],
                'font-src': ["'self'", "data:"],
                'connect-src': ["'self'"] + cors_origins,
            },
            content_security_policy_nonce_in=['script-src'],
            frame_options='DENY',
            referrer_policy='strict-origin-when-cross-origin',
            feature_policy={
                'geolocation': "'none'",
                'microphone': "'none'",
                'camera': "'none'",
            }
        )
    else:
        # In development, initialize with permissive settings
        talisman.init_app(
            app,
            force_https=False,
            strict_transport_security=False,
            content_security_policy={},
            frame_options='SAMEORIGIN'
        )
