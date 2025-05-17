import os
import time
import threading
import logging
import argparse
from flask import Flask, render_template, request, jsonify
from app import create_app
from app.config import Config
from app.database import get_db
from app.services.matlab_interface import get_matlab
from app.services.monitor_service import get_monitor_service
from app.services.event_service import get_event_service
from app.utils import get_logger
from app.utils.logger import Logger

# Parse command-line arguments
parser = argparse.ArgumentParser(description='ASTRA - Automated Satellite Threshold Reporting & Alerts')
parser.add_argument('--no-logging', action='store_true', help='Disable all logging')
args = parser.parse_args()

# Load configuration
config = Config()

# Set logging status - command line overrides environment variable
logging_enabled = not args.no_logging and config.is_logging_enabled()
Logger.set_enabled(logging_enabled)

# Configure logging
if logging_enabled:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("astra.log"),
            logging.StreamHandler()
        ]
    )
else:
    # Set up a null handler for root logger if logging is disabled
    logging.basicConfig(handlers=[logging.NullHandler()])

logger = logging.getLogger(__name__)

# Create application
app = create_app()

# Create required directories
os.makedirs("data", exist_ok=True)
os.makedirs("matlab_scripts", exist_ok=True)

# Check if we're in simulation mode
use_simulation = config.is_simulation_mode()
if use_simulation:
    logger.info("*** USING SIMULATION MODE - NO REAL MATLAB SCRIPTS WILL BE EXECUTED ***")
    logger.info("    (Set USE_SIMULATION=False in config/metrics_config.json file to use real MATLAB)")
else:
    logger.info("MATLAB integration enabled - will attempt to execute MATLAB scripts if present")

# Get database and MATLAB interface instances
db = get_db()
matlab = get_matlab()

def monitor_metrics():
    """Background thread to monitor satellite metrics at regular intervals."""
    logger.info("Starting background monitoring thread")
    
    while True:
        try:
            logger.info("Running scheduled metrics check")
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
            
            logger.info(f"Monitored {len(results)} metrics, found {sum(1 for r in results if r['status'] == 'BREACH')} breaches")
        except Exception as e:
            logger.error(f"Error in monitoring thread: {e}")
        
        # Sleep until next interval
        interval = config.get_refresh_interval()
        logger.info(f"Sleeping for {interval} seconds until next check")
        time.sleep(interval)

@app.route('/')
def index():
    """Render the dashboard page."""
    return render_template('dashboard.html')

@app.route('/events')
def events():
    """Render the events page."""
    return render_template('events.html')

if __name__ == "__main__":
    # Start the background monitoring thread
    monitor_thread = threading.Thread(target=monitor_metrics, daemon=True)
    monitor_thread.start()
    
    print("\n" + "="*80)
    print("ASTRA - Automated Satellite Threshold Reporting & Alerts")
    print("="*80)
    print(f"- Monitoring {len(config.get_payloads())} payloads and {len(config.get_metrics())} metrics")
    print(f"- Database: {config.get_database_path()}")
    print(f"- MATLAB scripts path: {config.get_matlab_scripts_path()}")
    print(f"- Simulation mode: {'ENABLED' if use_simulation else 'DISABLED'}")
    print(f"- Refresh interval: {config.get_refresh_interval()} seconds")
    print(f"- Logging: {'DISABLED' if not logging_enabled else 'ENABLED'}")
    print("\nAccessing the web interface:")
    print("- Dashboard: http://localhost:5000/")
    print("- Events: http://localhost:5000/events")
    print("="*80 + "\n")
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=True) 