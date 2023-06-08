import os
import urllib.parse
from typing import List

import jinja2
import requests
from bs4 import BeautifulSoup

from rss_downloader import helpers
from rss_downloader.config import settings

logger = helpers.setup_logging()


def fetch_event_entries(url: str) -> List[BeautifulSoup]:
    """
    Fetch event entries from a given URL.

    Parameters:
        url (str): The URL of the webpage to fetch event entries from.

    Returns:
        List: A list of BeautifulSoup Tag objects representing event entries.

    Raises:
        requests.exceptions.RequestException: If an error occurs while making the HTTP request.
    """

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching event entries: {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    event_entries = soup.find_all(
        "article",
        class_=(
            "SP-Teaser SP-Grid__full SP-Teaser--event SP-Teaser--hasLinks"
            " SP-Teaser--textual"
        ),
    )
    return event_entries


def fetch_event_image_url(event_url: str) -> str:
    """
    Fetch the image URL for an event.

    Parameters:
        event_url (str): The URL of the event.

    Returns:
        str: The fetched image URL or the default image URL if fetching fails.
    """
    default_event_img_url = settings.default.default_event_img_url

    if not event_url:
        return None

    try:
        webpage_response = requests.get(event_url, timeout=10)
        webpage_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching event image URL: {e}")
        return None

    webpage_soup = BeautifulSoup(webpage_response.content, "html.parser")
    picture_tag = webpage_soup.select_one("picture")

    if picture_tag:
        img_tag = picture_tag.find("img")
        if img_tag:
            image_url = urllib.parse.urljoin(event_url, img_tag.get("src"))
            php_file_name = os.path.basename(event_url)
            php_file_name = os.path.splitext(php_file_name)[0]

            if php_file_name in image_url:
                return image_url

    if default_event_img_url:
        # Check if default_event_img_url is a valid URL
        if urllib.parse.urlparse(default_event_img_url).scheme:
            return default_event_img_url
        logger.error(f"Invalid default_event_img_url: {default_event_img_url}")
        return default_event_img_url
    return None


def generate_google_maps_link(location: str) -> str:
    """
    Generate a Google Maps link for a location.

    Parameters:
        location (str): The location string.

    Returns:
        str: The generated Google Maps link.
    """

    if not location:
        return None
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(location)}"


def render_event_html(
    event_data: dict,
    image_url: str,
    google_maps_link: str,
    entrance_fee: str or None,
    extended_description: str or None,
    exhibition_hours_html: str or None,
    ical_link: str,
) -> str:
    """
    Render the HTML content for an event.

    Parameters:
        - event_data (dict): The event data dictionary.
        - image_url (str): The URL of the event image.
        - google_maps_link (str): The Google Maps link for the event location.
        - entrance_fee (str or None): The entrance fee for the event.
        - extended_description (str or None): The extended description of the event.
        - exhibition_hours_html (str or None): The HTML content for exhibition hours.
        - ical_link (str): The iCal link for the event.

    Returns:
        str: The rendered HTML content for the event.
    """
    template_directory = os.path.join(helpers.PROJECT_ROOT, "templates")
    template_loader = jinja2.FileSystemLoader(searchpath=template_directory)
    template_env = jinja2.Environment(loader=template_loader, autoescape=True)
    template = template_env.get_template("event_template.html")

    rendered_html = template.render(
        event_data=event_data,
        image_url=image_url,
        google_maps_link=google_maps_link,
        entrance_fee=entrance_fee,
        extended_description=extended_description,
        exhibition_hours_html=exhibition_hours_html,
        ical_link=ical_link,
    )

    return rendered_html
