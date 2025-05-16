import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    """Centralized logging utility for the ASTRA application."""
    
    def __init__(self, name='astra'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
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
        
        # Add the handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        """Log an info message."""
        self.logger.info(message)
    
    def error(self, message, exc_info=None):
        """Log an error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
    
    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def critical(self, message, exc_info=None):
        """Log a critical message with optional exception info."""
        self.logger.critical(message, exc_info=exc_info)

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