from flask import Blueprint, render_template, request, jsonify, current_app, g
from app.database import Database
from app.config import Config
from app.matlab_interface import MatlabInterface
import datetime

# Create blueprint
main_bp = Blueprint('main', __name__)

# Create configuration instance
config = Config()

# Create a function to get or create the database connection for each request
def get_db():
    """Get or create a database connection for the current request."""
    if 'db' not in g:
        g.db = Database(config.get_database_path())
    return g.db

# Create a function to get or create the MATLAB interface for each request
def get_matlab():
    """Get or create a MATLAB interface for the current request."""
    if 'matlab' not in g:
        g.matlab = MatlabInterface(config)
    return g.matlab

@main_bp.teardown_request
def close_db(exception=None):
    """Close the database connection at the end of each request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@main_bp.route('/')
def index():
    """Render the main dashboard page."""
    # Get the database connection
    db = get_db()
    
    # Get date filters from request or use default (last 60 days)
    today = datetime.date.today() + datetime.timedelta(days=1)
    print("todaydate is",today)
    default_from_date = (today - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
    default_to_date = today.strftime('%Y-%m-%d')
    
    date_from = request.args.get('date_from', default_from_date)
    date_to = request.args.get('date_to', default_to_date)
    
    # Create filter dictionary
    filters = {
        'date_from': date_from,
        'date_to': date_to
    }
    
    # Get breach counts for the dashboard with date filtering
    breach_counts = db.get_breach_counts(filters=filters)
    
    # Get the list of payloads and metrics from config
    payloads = config.get_payloads()
    metrics = config.get_metrics()
    
    # Create a dictionary to hold breach counts for each payload and metric
    dashboard_data = {}
    for payload in payloads:
        scid = payload["scid"]
        dashboard_data[scid] = {
            "name": payload["name"],
            "metrics": {}
        }
        
        # Initialize each metric with zero breaches
        for metric_name in metrics:
            dashboard_data[scid]["metrics"][metric_name] = {
                "count": 0,
                "threshold": config.get_threshold(metric_name),
                "status": "NORMAL"  # Default status
            }
    
    # Update breach counts from the database
    for breach in breach_counts:
        scid = breach["scid"]
        metric_type = breach["metric_type"]
        count = breach["count"]
        
        if scid in dashboard_data and metric_type in dashboard_data[scid]["metrics"]:
            dashboard_data[scid]["metrics"][metric_type]["count"] = count
    
    # Get the latest status for each payload and metric within the date range
    latest_statuses = db.get_latest_statuses(filters=filters)
    for status in latest_statuses:
        scid = status["scid"]
        metric_type = status["metric_type"]
        current_status = status["status"]
        
        if scid in dashboard_data and metric_type in dashboard_data[scid]["metrics"]:
            dashboard_data[scid]["metrics"][metric_type]["status"] = current_status
    
    return render_template('dashboard.html', 
                          dashboard_data=dashboard_data,
                          metrics=metrics,
                          date_from=date_from,
                          date_to=date_to)

@main_bp.route('/events')
def events():
    """Render the events table page."""
    # Get the database connection
    db = get_db()
    
    # Get date filters from request or use default (last 60 days)
    today = datetime.date.today() + datetime.timedelta(days=1)
    default_from_date = (today - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
    default_to_date = today.strftime('%Y-%m-%d')
    
    # Get filters from request
    filters = {}
    if request.args.get('scid'):
        filters['scid'] = int(request.args.get('scid'))
    if request.args.get('metric_type'):
        filters['metric_type'] = request.args.get('metric_type')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    # Apply date filters with defaults if not provided
    filters['date_from'] = request.args.get('date_from', default_from_date)
    filters['date_to'] = request.args.get('date_to', default_to_date)
    
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'timestamp')
    sort_order = request.args.get('sort_order', 'DESC')
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 100))
    offset = (page - 1) * page_size
    
    # Get events from database
    events = db.get_all_triggers(limit=page_size, offset=offset, 
                                sort_by=sort_by, sort_order=sort_order,
                                filters=filters)
    
    # Get total count for pagination
    total_count = db.get_trigger_count(filters=filters)
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    # Get the list of payloads and metrics from config for filter dropdowns
    payloads = config.get_payloads()
    metrics = config.get_metrics()
    
    return render_template('events.html',
                          events=events,
                          payloads=payloads,
                          metrics=metrics,
                          filters=filters,
                          page=page,
                          page_size=page_size,
                          total_pages=total_pages,
                          total_count=total_count,
                          limit=page_size,
                          sort_by=sort_by,
                          sort_order=sort_order)

@main_bp.route('/api/monitor', methods=['POST'])
def monitor():
    """Run the monitoring process manually."""
    # Get the database and MATLAB connections
    db = get_db()
    matlab = get_matlab()
    
    results = matlab.monitor_all_metrics()
    
    # Log results to database
    for result in results:
        db.log_trigger(
            scid=result["scid"],
            metric_type=result["metric_type"],
            timestamp=result["timestamp"],
            value=result["value"],
            threshold=result["threshold"],
            status=result["status"]
        )
    
    return jsonify({
        "status": "success",
        "message": f"Monitored {len(results)} metrics",
        "results": results
    })

@main_bp.route('/api/events')
def api_events():
    """API endpoint to get events in JSON format."""
    # Get the database connection
    db = get_db()
    
    # Same filtering logic as events route
    filters = {}
    if request.args.get('scid'):
        filters['scid'] = int(request.args.get('scid'))
    if request.args.get('metric_type'):
        filters['metric_type'] = request.args.get('metric_type')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'timestamp')
    sort_order = request.args.get('sort_order', 'DESC')
    
    # Get pagination parameters
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Get events from database
    events = db.get_all_triggers(limit=limit, offset=offset, 
                                sort_by=sort_by, sort_order=sort_order,
                                filters=filters)
    
    # Convert row objects to dictionaries
    events_dict = [dict(event) for event in events]
    
    return jsonify(events_dict)

@main_bp.route('/api/breach_history')
def api_breach_history():
    db = get_db()
    scid = request.args.get('scid', type=int)
    metric_type = request.args.get('metric_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # Default: last 7 days if not provided
    today = datetime.date.today()
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')
    if not date_from:
        date_from = (today - datetime.timedelta(days=6)).strftime('%Y-%m-%d')

    rows = db.get_breach_history(scid, metric_type, date_from, date_to)
    return jsonify(rows) 