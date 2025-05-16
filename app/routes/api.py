from flask import Blueprint, jsonify, request
from app.services import get_event_service, get_monitor_service
from app.utils import get_logger
from .utils import (
    get_matlab, parse_filter_params, parse_pagination_params,
    parse_sort_params, handle_error, validate_required_params
)

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

@api_bp.route('/events')
def get_events():
    """Get events in JSON format."""
    try:
        # Get filters, pagination, and sorting parameters using utility functions
        filters = parse_filter_params(request)
        page, page_size = parse_pagination_params(request)
        sort_by, sort_order = parse_sort_params(request)
        
        # Get events from event service
        result = get_event_service().get_events(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        return jsonify({
            'success': True,
            'data': {
                'events': result['events'],
                'total_pages': result['total_pages'],
                'total_count': result['total_count'],
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
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