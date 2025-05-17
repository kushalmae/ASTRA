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
    ## GET The Json File Variables
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
            return {}
    
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
    
    def get_environment(self, key, default=None):
        """Get a value from the environment configuration in the JSON file. """
        env_config = self.config.get("environment", {})
        # First try the JSON config
        if key in env_config:
            return env_config[key]
    
    def get_matlab_scripts_path(self):
        """Get the path to MATLAB scripts from configuration."""
        return self.get_environment("MATLAB_SCRIPTS_PATH", "./matlab_scripts")
    
    def get_refresh_interval(self):
        """Get the refresh interval from configuration."""
        interval = self.get_environment("REFRESH_INTERVAL", "600")
        return int(interval)
    
    def get_database_path(self):
        """Get the database path from configuration."""
        return self.get_environment("DATABASE_PATH", "./data/astra.db")
        
    def is_logging_enabled(self):
        """Determine if logging is enabled from configuration.
        
        This can be used to disable all logging in the application by setting
        the LOGGING_ENABLED environment variable to 'False', '0', or 'no'.
        
        Returns:
            bool: True if logging is enabled, False otherwise.
        """
        value = self.get_environment("LOGGING_ENABLED", "True").lower()
        return value not in ("false", "0", "no")
        
    def is_simulation_mode(self):
        """Determine if simulation mode is enabled from configuration.
        
        Returns:
            bool: True if simulation mode is enabled, False otherwise.
        """
        value = self.get_environment("USE_SIMULATION", "False").lower()
        return value in ("true", "1", "yes") 