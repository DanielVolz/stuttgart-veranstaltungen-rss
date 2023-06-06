import logging
import os


def setup_logging() -> logging.Logger:
    """
    Set up logging for the RSS generator.

    Returns:
        logging.Logger: The logger object for logging events.
    """

    log_file = "rss_downloader.log"
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()],
    )
    log = logging.getLogger(__name__)

    return log
