"""Application factory module."""

from flask import Flask
from app.config.config import Config
from app.database import get_db
from app.routes.main import main_bp
from app.routes.api import api_bp
from app.utils import get_logger
from app.config.cache import cache, init_cache

# Initialize logger
logger = get_logger('app')

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize database
    db = get_db()
    db.init_app()
    
    # Initialize cache with app
    init_cache(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register teardown function to close database resources
    @app.teardown_appcontext
    def cleanup(exception=None):
        db = get_db()
        db.close_session()
    
    return app 