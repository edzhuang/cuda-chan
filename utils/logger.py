"""Logging configuration for CUDA-chan."""

import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger():
    """Configure the logger with appropriate settings."""
    # Remove default logger
    logger.remove()

    # Get log level from settings
    log_level = settings.system.log_level

    # Console output (colorized)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File output (detailed, includes all logs)
    logs_dir = settings.get_logs_dir()
    logger.add(
        logs_dir / "cuda_chan_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",  # Always capture debug in files
        rotation="00:00",  # New file at midnight
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress old logs
    )

    # Error-specific log file
    logger.add(
        logs_dir / "cuda_chan_errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="zip",
    )

    logger.info("Logger initialized")
    logger.debug(f"Log level set to: {log_level}")
    logger.debug(f"Logs directory: {logs_dir}")

    return logger


# Create a global logger instance
log = setup_logger()


if __name__ == "__main__":
    # Test the logger
    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.success("This is a success message")
