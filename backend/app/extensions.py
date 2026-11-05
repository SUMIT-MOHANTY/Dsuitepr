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


def init_extensions(app):
    """Initialize all Flask extensions with the app instance.
    
    Args:
        app: Flask application instance
    """
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'api.auth_login'
    login_manager.login_message = 'Please log in to access this resource.'
    login_manager.login_message_category = 'info'
    
    # Initialize CORS with configuration from app config
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
                "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
            }
        }
    )
    
    # Initialize Rate Limiter
    limiter.init_app(app)
