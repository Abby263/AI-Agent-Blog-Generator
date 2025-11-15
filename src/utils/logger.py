"""
Logging configuration and utilities.

Provides comprehensive logging for all agents and workflow steps.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from src.utils.config_loader import get_config


def setup_logger(
    name: str = "blog_generator",
    log_file: Optional[str] = None,
    log_level: Optional[str] = None
) -> logging.Logger:
    """
    Set up logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Log file path (None to use config)
        log_level: Log level (None to use config)
        
    Returns:
        Configured logger instance
    """
    config = get_config()
    
    # Get log configuration
    if log_level is None:
        log_level = config.get("monitoring.logging.level", "INFO")
    
    if log_file is None:
        log_file = config.get("monitoring.logging.file", "logs/workflow.log")
    
    log_format = config.get(
        "monitoring.logging.format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (with rotation)
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        max_bytes = config.get("monitoring.logging.max_bytes", 10485760)
        backup_count = config.get("monitoring.logging.backup_count", 5)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """
    Get or create global logger instance.
    
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger

