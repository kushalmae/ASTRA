import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from app.config import Config

# Special null handler that does nothing
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

class Logger:
    """Centralized logging utility for the ASTRA application."""
    
    # Class variable to track global logging state
    _logging_enabled = True
    
    @classmethod
    def set_enabled(cls, enabled):
        """Enable or disable all logging globally.
        
        Args:
            enabled (bool): Whether logging should be enabled
        """
        cls._logging_enabled = enabled
        
    @classmethod
    def is_enabled(cls):
        """Check if logging is enabled globally.
        
        Returns:
            bool: True if logging is enabled, False otherwise
        """
        # Check both the class variable and the config setting
        config = Config()
        return cls._logging_enabled and config.is_logging_enabled()
    
    def __init__(self, name='astra'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.name = name
        
        # Always configure handlers on init, but they may be disabled later
        self._configure_handlers()
        
    def _configure_handlers(self):
        """Configure and set up all handlers for the logger."""
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # File handler for all logs
        file_handler = RotatingFileHandler(
            'logs/astra.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # File handler for errors only
        error_handler = RotatingFileHandler(
            'logs/error.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters and add them to the handlers
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'File: %(pathname)s\n'
            'Line: %(lineno)d\n'
            'Function: %(funcName)s\n'
            'Exception: %(exc_info)s'
        )
        
        file_handler.setFormatter(file_formatter)
        error_handler.setFormatter(error_formatter)
        console_handler.setFormatter(file_formatter)
        
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def _log_if_enabled(self, level, message, **kwargs):
        """Only log if logging is enabled.
        
        Args:
            level: The logging level method to call
            message: The message to log
            **kwargs: Additional arguments to pass to the logging method
        """
        if self.is_enabled():
            level(message, **kwargs)
    
    def info(self, message):
        """Log an info message."""
        self._log_if_enabled(self.logger.info, message)
    
    def error(self, message, exc_info=None):
        """Log an error message with optional exception info."""
        self._log_if_enabled(self.logger.error, message, exc_info=exc_info)
    
    def warning(self, message):
        """Log a warning message."""
        self._log_if_enabled(self.logger.warning, message)
    
    def debug(self, message):
        """Log a debug message."""
        self._log_if_enabled(self.logger.debug, message)
    
    def critical(self, message, exc_info=None):
        """Log a critical message with optional exception info."""
        self._log_if_enabled(self.logger.critical, message, exc_info=exc_info)

# Create a singleton instance for the main application
main_logger = Logger()

def get_logger(name=None):
    """Get a logger instance.
    
    Args:
        name (str, optional): The name of the logger. If None, returns the main application logger.
    
    Returns:
        Logger: A logger instance.
    """
    if name is None:
        return main_logger
    return Logger(name) 