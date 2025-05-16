import os
import time
import threading
import logging
from app import create_app
from app.config import Config
from app.database import Database
from app.matlab_interface import MatlabInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("astra.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create application
app = create_app()

# Create required directories
os.makedirs("data", exist_ok=True)
os.makedirs("matlab_scripts", exist_ok=True)

# Load configuration
config = Config()

# Check if we're in simulation mode
use_simulation = os.getenv("USE_SIMULATION", "False").lower() in ("true", "1", "yes")
if use_simulation:
    logger.info("*** USING SIMULATION MODE - NO REAL MATLAB SCRIPTS WILL BE EXECUTED ***")
    logger.info("    (Set USE_SIMULATION=False in .env file to use real MATLAB)")
else:
    logger.info("MATLAB integration enabled - will attempt to execute MATLAB scripts if present")

# Create database and MATLAB interface instances
# Note: We'll create a separate database instance for the monitoring thread
db = Database(config.get_database_path())
matlab = MatlabInterface(config)

def monitor_metrics():
    """Background thread to monitor satellite metrics at regular intervals."""
    logger.info("Starting background monitoring thread")
    
    # Create a separate database instance for this thread
    monitor_db = Database(config.get_database_path())
    
    while True:
        try:
            logger.info("Running scheduled metrics check")
            results = matlab.monitor_all_metrics()
            
            # Log results to database
            for result in results:
                monitor_db.log_trigger(
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
    print("\nAccessing the web interface:")
    print("- Dashboard: http://localhost:5000/")
    print("- Events: http://localhost:5000/events")
    print("="*80 + "\n")
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=True) 