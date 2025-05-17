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
        self.use_simulation = self.config.is_simulation_mode()
        logger.info("use_simulation: " + str(self.use_simulation))
        os.makedirs(self.matlab_path, exist_ok=True)
        self.engine = None
        self.initialized = False    
  
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
            logger.info("cmd: " + str(cmd))
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
    
# Create a singleton instance
matlab_interface = MatlabInterface()

def get_matlab():
    """Get the singleton MATLAB interface instance."""
    return matlab_interface 