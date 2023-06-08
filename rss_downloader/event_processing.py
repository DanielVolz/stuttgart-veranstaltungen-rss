import urllib.parse
import xml.etree.ElementTree as ET
from email.utils import formatdate
from typing import Tuple

import ics
import pytz
import requests
from bs4 import BeautifulSoup

from rss_downloader import helpers, web_utils

logger = helpers.setup_logging()


def process_event_entry(
    event_entry: BeautifulSoup, url: str, channel: ET.Element
) -> None:
    """
    Process an event entry by extracting event information, building event HTML,
    and adding the event to a channel.

    Parameters:
        - event_entry (BeautifulSoup): The HTML tag representing the event entry.
        - url (str): The base URL of the event.
        - channel (xml.etree.ElementTree.Element): The XML element representing the channel.

    Returns:
        None
    """

    ical_link, event = extract_event_info_from_ical(event_entry, url)
    event_html = build_event_html(event, ical_link)
    add_event_to_channel(event, event_html, channel)


def extract_event_info_from_ical(
    event_entry: BeautifulSoup, url: str
) -> Tuple[str, ics.Event]:
    """
    Extract event information from an event entry.

    Parameters:
        - event_entry (BeautifulSoup): The HTML tag representing the event entry.
        - url (str): The base URL of the event.

    Returns:
        Tuple[str, ics.Event]: A tuple containing the extracted iCal link and the event object.
    """

    ical_link_element = event_entry.select_one(
        ".SP-Teaser__links .SP-Link.SP-Iconized--left"
    )
    ical_link = urllib.parse.urljoin(url, ical_link_element["href"])
    ical_link = urllib.parse.unquote(ical_link)
    ical_response = requests.get(ical_link, timeout=10)
    ical_data = ical_response.text
    cal = ics.Calendar(ical_data)
    event = list(cal.events)[0]
    return ical_link, event


def build_event_html(event: ics.Event, ical_link: str) -> str:
    """
    Build HTML content for an event.

    Parameters:
        - event (ics.Event): The event object.
        - ical_link (str): The iCal link of the event.

    Returns:
        str: The generated HTML content for the event.
    """

    event_data = extract_event_data(event)
    image_url = web_utils.fetch_event_image_url(event_data["url"])
    google_maps_link = web_utils.generate_google_maps_link(event_data["location"])
    entrance_fee = parse_entrance_fee(event_data["url"])
    extended_description = parse_extended_description(event_data["url"])
    exhibition_hours_html = parse_exhibition_hours(event_data["url"])

    event_html = web_utils.render_event_html(
        event_data,
        image_url,
        google_maps_link,
        entrance_fee,
        extended_description,
        exhibition_hours_html,
        ical_link,
    )
    return event_html


def extract_event_data(event: ics.Event) -> dict:
    """
    Extract event data from an event object.

    Parameters:
        event (ics.Event): The event object.

    Returns:
        dict: A dictionary containing the extracted event data.
    """

    germany_tz = pytz.timezone("Europe/Berlin")
    event_start = event.begin.astimezone(germany_tz)
    event_end = event.end.astimezone(germany_tz)

    return {
        "title": event.name,
        "start_time": event_start.strftime("%H:%M Uhr"),
        "end_time": event_end.strftime("%H:%M Uhr"),
        "date": event_start.strftime("%a, %d %b %Y"),
        "location": event.location,
        "description": event.description,
        "url": event.url,
        "categories": event.categories,
        "tags_str": ", ".join(event.categories),
    }


def parse_entrance_fee(event_url: str) -> str or None:
    """
    Parse the entrance fee for an event.

    Parameters:
        event_url (str): The URL of the event.

    Returns:
        str or None: The parsed entrance fee or None if parsing fails.
    """

    if not event_url:
        return None

    try:
        webpage_response = requests.get(event_url, timeout=10)
        webpage_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error parsing entrance fee: {e}")
        return None

    webpage_soup = BeautifulSoup(webpage_response.content, "html.parser")
    entrance_fee_element = webpage_soup.select_one(
        ".SP-CallToAction__text .SP-Paragraph p"
    )

    if entrance_fee_element and entrance_fee_element.contents:
        return entrance_fee_element.contents[0].strip()


def parse_extended_description(event_url: str) -> str or None:
    """
    Parse the extended description for an event.

    Parameters:
        event_url (str): The URL of the event.

    Returns:
        str or None: The parsed extended description or None if parsing fails.
    """

    if not event_url:
        return None

    webpage_response = requests.get(event_url, timeout=10)
    webpage_soup = BeautifulSoup(webpage_response.content, "html.parser")
    extended_description_elements = webpage_soup.select(
        ".SP-ArticleContent .SP-Text:not(.SP-Text--notice) .SP-Paragraph"
        " p:not(.SP-CallToAction__text .SP-Paragraph p)"
    )

    for element in extended_description_elements:
        br_tags = element.find_all("br")
        for br_tag in br_tags:
            br_tag.replace_with("\n")

    return "\n".join(
        [element.text.strip() for element in extended_description_elements]
    )


def parse_exhibition_hours(event_url: str) -> str or None:
    """
    Parse the exhibition hours for an event.

    Parameters:
        event_url (str): The URL of the event.

    Returns:
        str or None: The parsed exhibition hours or None if parsing fails.
    """

    if not event_url:
        return None

    webpage_response = requests.get(event_url, timeout=10)
    webpage_soup = BeautifulSoup(webpage_response.content, "html.parser")
    exhibition_hours = webpage_soup.find(
        "section",
        class_=(
            "SP-Text SP-Text--boxed SP-Grid__full--background"
            " SP-Grid__full--backgroundHighlighted"
        ),
    )

    if exhibition_hours:
        exhibition_hours_div = exhibition_hours.find("div")
        if exhibition_hours_div:
            return "".join(map(str, exhibition_hours_div.contents))


def add_event_to_channel(
    event: ics.Event, event_html: str, channel: ET.Element
) -> None:
    """
    Add an event to the XML channel.

    Parameters:
        - event (ics.Event): The event object.
        - event_html (str): The HTML content for the event.
        - channel (ElementTree.Element): The XML element representing the channel.

    Returns:
        None
    """

    event_title = event.name
    event_start = event.begin
    pub_date = formatdate(event_start.datetime.timestamp(), usegmt=True)

    event_exists = False
    for existing_item in channel.findall("item"):
        existing_title_element = existing_item.find("title")
        if existing_title_element is None:
            continue

        existing_title = existing_title_element.text
        existing_pub_date = existing_item.find("pubDate").text
        if existing_title == event_title and existing_pub_date == pub_date:
            event_exists = True
            logger.info(
                f"Skip adding event (duplicate): {event_title}, date: {pub_date}"
            )
            break

    if event_exists:
        return

    # Add the event to the rss channel
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = event_title
    ET.SubElement(item, "description").text = event_html
    ET.SubElement(item, "link").text = event.url
    ET.SubElement(item, "pubDate").text = pub_date
    logger.info(f"Added event to rss file: {event_title}, date: {pub_date}")
