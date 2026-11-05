"""Flask application factory."""

from flask import Flask
from backend.app.config import get_config
from backend.app.extensions import init_extensions, db
from backend.app.api import register_api_blueprints


def create_app(config_name=None):
    """Create and configure the Flask application.
    
    Args:
        config_name: Configuration environment name (development, production, testing)
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config() if config_name is None else get_config()
    app.config.from_object(config)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_api_blueprints(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
