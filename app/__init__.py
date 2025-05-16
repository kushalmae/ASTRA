from flask import Flask, g
from app.config import Config

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = Config()
    app.config['DATABASE_PATH'] = config.get_database_path()
    
    # Add custom template filters
    @app.template_filter('min')
    def min_filter(*args):
        """Return the minimum value from the arguments.
        This filter can handle both individual values or a list/array.
        """
        if len(args) == 1 and isinstance(args[0], list):
            return min(args[0])
        return min(args)
    
    @app.template_filter('max')
    def max_filter(*args):
        """Return the maximum value from the arguments.
        This filter can handle both individual values or a list/array.
        """
        if len(args) == 1 and isinstance(args[0], list):
            return max(args[0])
        return max(args)
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    @app.teardown_appcontext
    def close_resources(error):
        """Ensure all resources are closed when the request ends."""
        db = g.pop('db', None)
        if db is not None:
            db.close()
    
    return app 