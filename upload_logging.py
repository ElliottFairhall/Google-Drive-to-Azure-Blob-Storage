import logging
import os


def get_logger():
    """
    This function sets up logging for the application.
    """
    # Set up logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Set up file handler
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log_file = os.path.join(log_dir, 'upload.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

logger = get_logger()
