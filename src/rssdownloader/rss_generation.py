import os
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

from rssdownloader import (
    calendar_utils,
    event_processing,
    helpers,
    rss_utils,
    web_utils,
)

logger = helpers.setup_logging()


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
        date_list = calendar_utils.create_date_list()

        for date in date_list:
            date_str = date.strftime("%Y-%m-%d")
            url = f"https://www.stuttgart.de/service/veranstaltungen.php?form=eventSearch-1.form&sp:dateFrom[]={date_str}&sp:dateTo[]={date_str}&sp:categories[77306][]={rss_category}&action=submit"

            event_entries = web_utils.fetch_event_entries(url)

            for event_entry in event_entries:
                event_processing.process_event_entry(event_entry, url, channel)

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
    rss_directory = os.path.join(helpers.PROJECT_ROOT, "rss")
    rss_path = os.path.join(rss_directory, rss_name)

    if not os.path.exists(rss_directory):
        os.makedirs(rss_directory)

    rss_data = ET.tostring(rss, encoding="utf-8")

    try:
        with open(rss_path, "w", encoding="utf-8") as f:
            f.write(rss_data.decode("utf-8"))
    except IOError as e:
        logger.error(f"Failed to write RSS data to '{rss_path}': {e}")
        return

    logger.info(f"{rss_utils.count_events(rss_path)} events added to '{rss_name}'.")
    logger.info(f"RSS feed '{rss_name}' in '{rss_directory}' generated successfully!")
