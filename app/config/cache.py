from flask_caching import Cache
import os

cache = Cache()

def init_cache(app):
    """Initialize Flask-Caching with the application."""
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(app.root_path, '..', 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_config = {
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': cache_dir,
        'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes
        'CACHE_THRESHOLD': 1000,  # Maximum number of items the cache will store
        'CACHE_OPTIONS': {
            'mode': 0o600  # File permissions
        }
    }
    
    # Override with environment variables if present
    if app.config.get('CACHE_TYPE'):
        cache_config['CACHE_TYPE'] = app.config['CACHE_TYPE']
    if app.config.get('CACHE_DEFAULT_TIMEOUT'):
        cache_config['CACHE_DEFAULT_TIMEOUT'] = app.config['CACHE_DEFAULT_TIMEOUT']
    
    cache.init_app(app, config=cache_config) 