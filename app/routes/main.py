from flask import Blueprint, render_template, request
from app.config import Config
from app.services import get_event_service, get_monitor_service
from app.utils import get_logger
from .utils import (
    parse_filter_params, parse_pagination_params,
    parse_sort_params, handle_error
)

# Initialize logger
logger = get_logger('main')

# Create blueprint
main_bp = Blueprint('main', __name__)

# Create configuration instance
config = Config()

@main_bp.route('/')
def index():
    """Render the main dashboard page."""
    try:
        # Get filters using utility function
        filters = parse_filter_params(request)
        logger.info(f"Dashboard filters: {filters}")
        
        # Get current status from monitor service
        dashboard_data = get_monitor_service().get_current_status(filters=filters)
        
        # Debug logging for dashboard data
        breach_count = 0
        breach_cells = 0
        
        for scid, payload_data in dashboard_data.items():
            for metric_name, metric_data in payload_data['metrics'].items():
                count = metric_data.get('count', 0)
                status = metric_data.get('status', 'NORMAL')
                breach_count += count
                if status == 'BREACH':
                    breach_cells += 1
                    logger.info(f"BREACH found: SCID {scid}, metric {metric_name}, count {count}, status {status}")
        
        logger.info(f"Dashboard summary: {len(dashboard_data)} payloads, {breach_count} total breaches, {breach_cells} cells in breach status")
        
        # Get the list of metrics from config
        metrics = config.get_metrics()
        
        return render_template('dashboard.html', 
                             dashboard_data=dashboard_data,
                             metrics=metrics,
                             date_from=filters['date_from'],
                             date_to=filters['date_to'])
    except Exception as e:
        return handle_error(e)

@main_bp.route('/events')
def events():
    """Render the events table page."""
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
        
        # Get the list of payloads and metrics from config for filter dropdowns
        payloads = config.get_payloads()
        metrics = config.get_metrics()
        
        return render_template('events.html',
                             events=result['events'],
                             payloads=payloads,
                             metrics=metrics,
                             filters=filters,
                             page=page,
                             page_size=page_size,
                             total_pages=result['total_pages'],
                             total_count=result['total_count'],
                             sort_by=sort_by,
                             sort_order=sort_order)
    except Exception as e:
        return handle_error(e) 