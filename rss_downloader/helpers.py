import logging
import os

PROJECT_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))


def setup_logging() -> logging.Logger:
    """
    Set up logging for the RSS generator.

    Returns:
        logging.Logger: The logger object for logging events.
    """

    # Create a new log directory path
    log_directory = os.path.join(PROJECT_ROOT, "log")
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file = "rss_downloader.log"
    log_file_path = os.path.join(log_directory, log_file)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    return logger
