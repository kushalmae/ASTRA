"""MATLAB interface service for interacting with MATLAB engine."""

import subprocess
import json
import os
import datetime
import random
import matlab.engine
from app.config import Config
from app.utils import get_logger

# Initialize logger
logger = get_logger('services.matlab')

class MatlabInterface:
    """Interface for interacting with MATLAB engine."""
    
    def __init__(self, config=None):
        """Initialize MATLAB interface."""
        self.config = config or Config()
        self.matlab_path = self.config.get_matlab_scripts_path()
        self.use_simulation = os.getenv("USE_SIMULATION", "False").lower() in ("true", "1", "yes")
        os.makedirs(self.matlab_path, exist_ok=True)
        self.engine = None
        self.initialized = False
    
    def start_engine(self):
        """Start MATLAB engine."""
        try:
            if not self.initialized:
                logger.info("Starting MATLAB engine...")
                self.engine = matlab.engine.start_matlab()
                self.initialized = True
                logger.info("MATLAB engine started successfully")
        except Exception as e:
            logger.error(f"Failed to start MATLAB engine: {str(e)}", exc_info=True)
            raise
    
    def stop_engine(self):
        """Stop MATLAB engine."""
        try:
            if self.initialized and self.engine:
                logger.info("Stopping MATLAB engine...")
                self.engine.quit()
                self.initialized = False
                logger.info("MATLAB engine stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop MATLAB engine: {str(e)}", exc_info=True)
            raise
    
    def run_script(self, script_name, payload_id=None):
        """Run a MATLAB script.
        
        Args:
            script_name (str): Name of the script to run
            payload_id (str, optional): Payload ID to pass to the script
            
        Returns:
            dict: Script execution results
        """
        try:
            script_path = os.path.join(self.matlab_path, script_name)
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script not found: {script_path}")
            
            if self.use_simulation:
                logger.info(f"Simulation mode: Would run {script_name} with payload {payload_id}")
                return self._simulate_script_results(script_name, payload_id)
            
            # Run the MATLAB script
            cmd = ["matlab", "-batch", f"run('{script_path}')"]
            if payload_id:
                cmd.extend(["-payload", payload_id])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Script execution failed: {result.stderr}")
            
            # Parse the JSON output from MATLAB
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse MATLAB output: {result.stdout}")
                raise
        except Exception as e:
            logger.error(f"Error running script {script_name}: {str(e)}", exc_info=True)
            raise
    
    def _simulate_script_results(self, script_name, payload_id=None):
        """Simulate script results for testing.
        
        Args:
            script_name (str): Name of the script
            payload_id (str, optional): Payload ID
            
        Returns:
            dict: Simulated results
        """
        # Generate some random data for testing
        return {
            "results": [{
                "timestamp": datetime.datetime.now(datetime.UTC),
                "scid": payload_id or "101",
                "metric_type": script_name.split('_')[1],
                "value": random.uniform(20, 30),
                "threshold": 25.0,
                "status": "NORMAL"
            }]
        }
    
    def monitor_all_metrics(self):
        """Monitor all configured metrics.
        
        Returns:
            list: List of monitoring results for each metric
        """
        try:
            # Get all metrics from config
            metrics = self.config.get_metrics()
            results = []
            
            # Run monitoring for each metric
            for metric_type in metrics:
                try:
                    metric_results = self.run_script(f"sample_{metric_type}_monitor.m")
                    if isinstance(metric_results, dict) and 'results' in metric_results:
                        # Convert string timestamps to datetime objects
                        for result in metric_results['results']:
                            if isinstance(result.get('timestamp'), str):
                                result['timestamp'] = datetime.datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                        results.extend(metric_results['results'])
                    elif isinstance(metric_results, list):
                        # Convert string timestamps to datetime objects
                        for result in metric_results:
                            if isinstance(result.get('timestamp'), str):
                                result['timestamp'] = datetime.datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                        results.extend(metric_results)
                except Exception as e:
                    logger.error(f"Error monitoring metric {metric_type}: {str(e)}")
                    continue
            
            return results
        except Exception as e:
            logger.error(f"Error monitoring metrics: {str(e)}", exc_info=True)
            raise
    
    def run_monitoring_metrics(self, scid, metric_type, value):
        """Run monitoring metrics in MATLAB.
        
        Args:
            scid (str): Spacecraft ID
            metric_type (str): Type of metric to monitor
            value (float): Current value of the metric
            
        Returns:
            dict: Monitoring results including threshold and status
        """
        try:
            if not self.initialized:
                self.start_engine()
            
            # Call MATLAB function to process metrics
            # Note: You'll need to implement the actual MATLAB function
            result = self.engine.process_metrics(scid, metric_type, value)
            
            return {
                'threshold': float(result['threshold']),
                'status': str(result['status'])
            }
        except Exception as e:
            logger.error(f"Error running monitoring metrics: {str(e)}", exc_info=True)
            raise
    
    def get_metric_threshold(self, scid, metric_type):
        """Get threshold for a specific metric.
        
        Args:
            scid (str): Spacecraft ID
            metric_type (str): Type of metric
            
        Returns:
            float: Threshold value for the metric
        """
        try:
            if not self.initialized:
                self.start_engine()
            
            # Call MATLAB function to get threshold
            # Note: You'll need to implement the actual MATLAB function
            threshold = self.engine.get_threshold(scid, metric_type)
            
            return float(threshold)
        except Exception as e:
            logger.error(f"Error getting metric threshold: {str(e)}", exc_info=True)
            raise

# Create a singleton instance
matlab_interface = MatlabInterface()

def get_matlab():
    """Get the singleton MATLAB interface instance."""
    return matlab_interface 