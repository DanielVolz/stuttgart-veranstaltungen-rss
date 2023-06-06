import os
import shutil
import xml.etree.ElementTree as ET

from rssdownloader import helpers

logger = helpers.setup_logging()


def count_events(xml_file: str) -> int:
    """
    Count the number of events in an XML file.

    Parameters:
        xml_file (str): The path to the XML file containing event data.

    Returns:
        int: The number of events found in the XML file.

    Raises:
        ET.ParseError: If an error occurs during parsing the XML.
        IOError: If an IO error occurs while accessing the XML file.
    """

    try:
        tree = ET.parse(xml_file)  # nosec
        root = tree.getroot()
        event_count = len(root.findall(".//item"))
        return event_count
    except ET.ParseError as parse_error:
        # Handle parse errors
        logger.error(f"Error parsing XML: {parse_error}")
        raise
    except IOError as io_error:
        # Handle IO errors
        logger.error(f"IO Error occurred: {io_error}")
        raise


def move_rss_files(destination_folder: str, enable_move: bool) -> None:
    """
    Move RSS files to a destination folder.

    Parameters:
        - destination_folder: The path to the destination folder.
        - enable_move: Indicates whether moving files is enabled or not.

    Returns:
        None
    """
    if not enable_move:
        logger.info("Moving rss file(s) is disabled.")
        return None

    if not destination_folder:
        logger.error("destination_folder is not set or empty.")
        return None

    rss_directory = os.path.join(helpers.PROJECT_ROOT, "rss")

    # Check if destination_folder exists and is a directory
    try:
        os.listdir(destination_folder)
    except FileNotFoundError as exc:
        raise ValueError(
            f"destination_folder does not exist: {destination_folder}"
        ) from exc
    except NotADirectoryError as exc:
        raise ValueError(
            f"destination_folder is not a directory: {destination_folder}"
        ) from exc

    file_list = os.listdir(rss_directory)
    files_moved = False

    for file_name in file_list:
        if file_name.endswith(".rss"):
            source_path = os.path.join(rss_directory, file_name)
            destination_path = os.path.join(destination_folder, file_name)
            shutil.move(source_path, destination_path)
            logger.info(
                f"Moved file '{file_name}' to '{os.path.abspath(destination_folder)}'"
            )
            files_moved = True

    if not files_moved:
        logger.warning("No rss file(s) to move to destination.")
