import logging
from logging.handlers import RotatingFileHandler
import os


def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with RotatingFileHandler and console output.

    Args:
        name (str): Name of the logger, typically `__name__`.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger
    
    env = os.getenv("ENV", "DEV") # Get environment from environment variable or default to "DEV"
    
    if env == "production":
        logger.setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)  # Set the default logging level

    # Log formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not os.path.exists('logs/'):
        os.makedirs('logs/')
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        'logs/app.log', maxBytes=5 * 1024 * 1024, backupCount=5  # 5MB per file, 5 backups
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
