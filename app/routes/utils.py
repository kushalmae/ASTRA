"""Common utilities for route handlers."""

import datetime
from flask import g, jsonify, render_template, request
from app.config import Config
from app.services import MatlabInterface
from app.utils import get_logger

# Initialize logger
logger = get_logger('routes.utils')

def get_default_date_range():
    """Get default date range for filtering (last 60 days)."""
    today = datetime.date.today()
    default_from_date = (today - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
    default_to_date = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')  # Add one day to include today
    return default_from_date, default_to_date

def get_matlab():
    """Get or create a MATLAB interface for the current request."""
    if 'matlab' not in g:
        g.matlab = MatlabInterface(Config())
    return g.matlab

def parse_filter_params(request):
    """Parse common filter parameters from request."""
    filters = {}
    
    # Parse numeric filters
    if request.args.get('scid'):
        filters['scid'] = int(request.args.get('scid'))
    
    # Parse string filters
    for param in ['metric_type', 'status']:
        if request.args.get(param):
            filters[param] = request.args.get(param)
    
    # Parse date filters
    default_from_date, default_to_date = get_default_date_range()
    filters['date_from'] = request.args.get('date_from', default_from_date)
    filters['date_to'] = request.args.get('date_to', default_to_date)
    
    return filters

def parse_pagination_params(request):
    """Parse pagination parameters from request."""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 25))
    return page, page_size

def parse_sort_params(request):
    """Parse sorting parameters from request."""
    sort_by = request.args.get('sort_by', 'timestamp')
    sort_order = request.args.get('sort_order', 'DESC')
    return sort_by, sort_order

def handle_error(e, template='error.html', status_code=500):
    """Handle errors consistently across routes."""
    error_message = str(e)
    logger.error(f"Error: {error_message}", exc_info=True)
    
    if request.is_json:
        return jsonify({
            'success': False,
            'error': error_message
        }), status_code
    
    return render_template(template, error=error_message), status_code

def validate_required_params(params, required):
    """Validate that all required parameters are present."""
    missing = [param for param in required if not params.get(param)]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}") 