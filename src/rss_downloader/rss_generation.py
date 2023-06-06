import os
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

from rss_downloader.calendar_utils import create_date_list
from rss_downloader.event_processing import process_event_entry
from rss_downloader.log_helper import setup_logging
from rss_downloader.rss_utils import count_events
from rss_downloader.web_utils import fetch_event_entries

logger = setup_logging()


def generate_rss_feed(rss_feeds: List[Dict[str, str]]) -> None:
    """
    Generate RSS feeds for multiple categories.

    Parameters:
        - rss_feeds (List[Dict[str, str]]): A list of dictionaries representing RSS feeds.
            Each dictionary should contain the following keys:
            - 'name': The name of the RSS feed file.
            - 'title': The title of the RSS feed.
            - 'category': The category of the RSS feed.

    Returns:
        None
    """

    if not rss_feeds:
        logger.error("rss_feeds parameter is not set or empty. Exiting.")
        sys.exit(1)

    logger.info("Start generating RSS feeds.")

    for rss_feed in rss_feeds:
        rss_name = rss_feed.get("name")
        rss_title = rss_feed.get("title")
        rss_category = rss_feed.get("category")

        if not rss_name or not rss_title or not rss_category:
            logger.warning(
                "One or more parameters in rss_feed are not set or empty. Skipping."
            )
            continue

        logger.info(
            f"Start scraping the RSS category '{rss_title}' into the file:"
            f" '{rss_name}'."
        )

        rss, channel = create_rss_element(rss_title)
        date_list = create_date_list()

        for date in date_list:
            date_str = date.strftime("%Y-%m-%d")
            url = f"https://www.stuttgart.de/service/veranstaltungen.php?form=eventSearch-1.form&sp:dateFrom[]={date_str}&sp:dateTo[]={date_str}&sp:categories[77306][]={rss_category}&action=submit"

            event_entries = fetch_event_entries(url)

            for event_entry in event_entries:
                process_event_entry(event_entry, url, channel)

        write_rss_to_file(rss, rss_name)


def create_rss_element(rss_title: str) -> Tuple[ET.Element, ET.Element]:
    """
    Create an RSS element with a title.

    Parameters:
        rss_title: The title of the RSS element.

    Returns:
        Tuple: A tuple containing the root RSS element and the channel element.
    """

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    title = ET.SubElement(channel, "title")
    copyright_stuttgart = ET.SubElement(channel, "copyright")
    copyright_stuttgart.text = "Copyright 2023, Landeshauptstadt Stuttgart"
    link = ET.SubElement(channel, "link")
    link.text = "https://www.stuttgart.de/service/veranstaltungen.php"
    title.text = rss_title

    return rss, channel


def write_rss_to_file(rss: ET.Element, rss_name: str) -> None:
    """
    Write the RSS feed to a file.

    Parameters:
        - rss (ElementTree.Element): The XML element representing the RSS feed.
        - rss_name (str): The name of the RSS feed file.

    Returns:
        None
    """

    script_directory = os.path.dirname(os.path.abspath(__file__))
    rss_path = os.path.join(script_directory, rss_name)

    rss_data = ET.tostring(rss, encoding="utf-8")

    try:
        with open(rss_path, "w", encoding="utf-8") as f:
            f.write(rss_data.decode("utf-8"))
    except IOError as e:
        logger.error(f"Failed to write RSS data to '{rss_path}': {e}")
        return

    logger.info(f"{count_events(rss_path)} events added.")
    logger.info(
        f"RSS feed '{rss_name}' in '{script_directory}' generated successfully!"
    )
