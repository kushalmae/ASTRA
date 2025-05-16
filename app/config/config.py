import json
import os
from dotenv import load_dotenv

# Try to load environment variables from .env file
# Look in multiple locations to make it more flexible
for env_file in ['.env', 'env', '../.env', '../env']:
    if os.path.exists(env_file):
        load_dotenv(env_file)
        break

class Config:
    def __init__(self, config_path="config/metrics_config.json"):
        """Initialize the configuration loader."""
        self.config_path = config_path
        self.config = self.load_config()
        
    def load_config(self):
        """Load the configuration from the JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading configuration: {e}")
            # Return a default configuration if the file doesn't exist or is invalid
            return {
                "metrics": {
                    "thermal": {"threshold": 75.0},
                    "voltage": {"threshold": 3.3},
                    "latency": {"threshold": 250}
                },
                "payloads": [
                    {"scid": 101, "name": "Payload 1"},
                    {"scid": 102, "name": "Payload 2"},
                    {"scid": 103, "name": "Payload 3"}
                ]
            }
    
    def get_metrics(self):
        """Get the metrics configuration."""
        return self.config.get("metrics", {})
    
    def get_payloads(self):
        """Get the payload configuration."""
        return self.config.get("payloads", [])
    
    def get_threshold(self, metric_type):
        """Get the threshold for a specific metric type."""
        metrics = self.get_metrics()
        metric = metrics.get(metric_type, {})
        return metric.get("threshold", 0)
    
    def get_matlab_scripts_path(self):
        """Get the path to MATLAB scripts from environment variables."""
        return os.getenv("MATLAB_SCRIPTS_PATH", "./matlab_scripts")
    
    def get_refresh_interval(self):
        """Get the refresh interval from environment variables."""
        try:
            return int(os.getenv("REFRESH_INTERVAL", "600"))
        except ValueError:
            return 600
    
    def get_database_path(self):
        """Get the database path from environment variables."""
        return os.getenv("DATABASE_PATH", "./data/astra.db")
        
    def is_logging_enabled(self):
        """Determine if logging is enabled from environment variables.
        
        This can be used to disable all logging in the application by setting
        the LOGGING_ENABLED environment variable to 'False', '0', or 'no'.
        
        Returns:
            bool: True if logging is enabled, False otherwise.
        """
        return os.getenv("LOGGING_ENABLED", "True").lower() not in ("false", "0", "no") 