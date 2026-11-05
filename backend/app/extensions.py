"""Flask extensions initialization."""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# SQLAlchemy ORM instance
db = SQLAlchemy()

# Flask-Login instance
login_manager = LoginManager()

# Flask-CORS instance
cors = CORS()

# Flask-Limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)


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
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get('CORS_ORIGINS', ['http://localhost:5173', 'http://localhost:3000']),
                "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token"],
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "expose_headers": ["Content-Type", "X-CSRF-Token"]
            }
        }
    )
    
    # Initialize Rate Limiter
    limiter.init_app(app)
