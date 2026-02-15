"""Logging configuration for the Google Drive to Azure sync application.

This module configures application-wide logging with both console and
file handlers, providing structured log output for monitoring and debugging.
"""

import logging
from pathlib import Path

# Log directory configuration
LOG_DIR = Path.cwd() / "logs"
LOG_FILE = LOG_DIR / "sync.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
) -> logging.Logger:
    """Configure and return the application logger.

    Sets up logging with both console and file handlers. The file handler
    creates a log file in the 'logs' directory.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
            Defaults to logging.INFO.
        log_file: Optional custom path for the log file.
            Defaults to 'logs/sync.log'.

    Returns:
        Configured Logger instance for the application.

    Example:
        >>> logger = setup_logging(level=logging.DEBUG)
        >>> logger.info("Application started")
    """
    # Create root logger for the application
    app_logger = logging.getLogger("gdrive_azure_sync")
    app_logger.setLevel(level)

    # Avoid adding duplicate handlers
    if app_logger.handlers:
        return app_logger

    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    # File handler
    log_path = log_file or LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    return app_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance for a specific module.

    Returns a child logger of the application logger, allowing
    module-specific logging while inheriting configuration.

    Args:
        name: Name for the logger, typically __name__ of the calling module.
            If None, returns the root application logger.

    Returns:
        Logger instance configured with application settings.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing file: %s", filename)
    """
    if name:
        return logging.getLogger(f"gdrive_azure_sync.{name}")
    return logging.getLogger("gdrive_azure_sync")


# Initialize the default logger on module import
logger = setup_logging()
