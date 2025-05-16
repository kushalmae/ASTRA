from flask import Blueprint, jsonify, request
from app.services import get_event_service, get_monitor_service
from app.utils import get_logger
from app.utils.logger import Logger
from .utils import (
    get_matlab, parse_filter_params, parse_pagination_params,
    parse_sort_params, handle_error, validate_required_params
)
from app.config import Config

# Initialize logger
logger = get_logger('api')

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/monitor', methods=['POST'])
def run_monitor():
    """Run the monitoring process manually."""
    try:
        # Get MATLAB interface using utility function
        matlab = get_matlab()
        
        # Run monitoring metrics
        result = matlab.monitor_all_metrics()
        
        # Log the results using monitor service
        get_monitor_service().log_monitoring_results(result)
        
        return jsonify({
            'success': True,
            'message': 'Monitoring completed successfully',
            'data': result
        })
    except Exception as e:
        return handle_error(e)

@api_bp.route('/toggle_logging', methods=['POST'])
def toggle_logging():
    """Toggle application logging on or off."""
    try:
        # Get current status
        current_status = Logger.is_enabled()
        
        # Check if a specific state was requested
        if request.json and 'enabled' in request.json:
            # Set to the requested state
            new_status = bool(request.json['enabled'])
        else:
            # Toggle current status
            new_status = not current_status
            
        # Update the logging status
        Logger.set_enabled(new_status)
        
        message = f"Logging has been {'enabled' if new_status else 'disabled'}"
        logger.info(message)  # This will only log if logging is now enabled
        
        return jsonify({
            'success': True,
            'message': message,
            'logging_enabled': new_status
        })
    except Exception as e:
        return handle_error(e)

@api_bp.route('/events')
def get_events():
    """Get events in JSON format."""
    try:
        # Get filters, pagination, and sorting parameters using utility functions
        filters = parse_filter_params(request)
        page, page_size = parse_pagination_params(request)
        sort_by, sort_order = parse_sort_params(request)
        
        logger.info(f"API events request: page={page}, sort_by={sort_by}, sort_order={sort_order}, filters={filters}")
        
        # Get events from event service
        result = get_event_service().get_events(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        # Map payload IDs to names for better display
        payloads = {str(p['scid']): p['name'] for p in Config().get_payloads()}
        
        # Enrich event data with payload names
        for event in result['events']:
            event['payload_name'] = payloads.get(str(event['scid']), f"Unknown ({event['scid']})")
        
        return jsonify({
            'success': True,
            'data': {
                'events': result['events'],
                'total_pages': result['total_pages'],
                'total_count': result['total_count'],
                'page': page,
                'page_size': page_size,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        })
    except Exception as e:
        logger.error(f"Error fetching events: {str(e)}", exc_info=True)
        return handle_error(e)

@api_bp.route('/breach_history')
def get_breach_history():
    """Get breach history for a specific payload and metric."""
    try:
        # Get required parameters
        params = {
            'scid': request.args.get('scid'),
            'metric_type': request.args.get('metric_type')
        }
        
        # Validate required parameters
        validate_required_params(params, ['scid', 'metric_type'])
        
        # Get date filters using utility function
        filters = parse_filter_params(request)
        
        # Get breach history from event service
        history = get_event_service().get_breach_history(
            scid=int(params['scid']),
            metric_type=params['metric_type'],
            date_from=filters['date_from'],
            date_to=filters['date_to']
        )
        
        return jsonify({
            'success': True,
            'data': history
        })
    except ValueError as e:
        return handle_error(e, status_code=400)
    except Exception as e:
        return handle_error(e) 