import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime as dt
import datetime
from email.utils import formatdate
import pytz
import os
import ics
import locale
import xml.etree.ElementTree as ET
import shutil
import subprocess
import json
import logging
import html

# Set up logging
log_file = "rss_generator.log"
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def count_events(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    event_count = len(root.findall(".//item"))

    return event_count


def update_nextcloud_news():
    output = subprocess.check_output(
        [
            "sudo",
            "docker",
            "exec",
            "--user",
            "www-data",
            "-it",
            "nextcloud-aio-nextcloud",
            "php",
            "occ",
            "news:feed:list",
            "danielvolz",
        ]
    )
    parsed_data = json.loads(output)
    nextcloud_news_feed_ids = [
        entry["id"]
        for entry in parsed_data
        if entry["url"].startswith("https://rss.danielvolz.org")
    ]

    def is_container_running(container_name):
        command = f"docker ps --filter name={container_name} --format '{{{{.Names}}}}'"
        output = subprocess.check_output(command, shell=True, text=True)
        running_containers = output.splitlines()
        return container_name in running_containers

    container_name = "nextcloud-aio-nextcloud"

    if is_container_running(container_name):
        # Execute each command
        logger.info("Updating Nextcloud News feeds.")
        for nextcloud_news_feed_id in nextcloud_news_feed_ids:
            commands = [
                f"sudo docker exec --user www-data -it nextcloud-aio-nextcloud php occ news:feed:read danielvolz {nextcloud_news_feed_id}",
                f"sudo docker exec --user www-data -it nextcloud-aio-nextcloud php occ news:updater:update-feed danielvolz {nextcloud_news_feed_id}",
            ]
            for command in commands:
                process = subprocess.Popen(command, shell=True)
                process.communicate()  # Wait for the command to complete for the command to complete
    else:
        logger.error(f"Container '{container_name}' is not running.")


def move_rss_log_files(destination_folder):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    source_folder = script_directory

    file_list = os.listdir(source_folder)
    for file_name in file_list:
        if file_name.endswith((".rss", ".log")):
            source_path = os.path.join(source_folder, file_name)
            destination_path = os.path.join(destination_folder, file_name)
            shutil.move(source_path, destination_path)
            logger.info("Moved file: %s", file_name)


def generate_rss_feed(rss_name, rss_title, rss_category):
    logger.info(
        f"Start scraping the RSS category {rss_title} in to the file: {rss_name}."
    )
    today = datetime.date.today()
    date_list = [today + datetime.timedelta(days=i) for i in range(7)]

    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    title = ET.SubElement(channel, "title")
    title.text = rss_title

    for date in date_list:
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://www.stuttgart.de/service/veranstaltungen.php?form=eventSearch-1.form&sp:dateFrom[]={date_str}&sp:dateTo[]={date_str}&sp:categories[77306][]={rss_category}&action=submit"

        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        link = ET.SubElement(channel, "link")
        link.text = url

        event_entries = soup.find_all(
            "article",
            class_="SP-Teaser SP-Grid__full SP-Teaser--event SP-Teaser--hasLinks SP-Teaser--textual",
        )
        for event_entry in event_entries:
            ical_link_element = event_entry.select_one(
                ".SP-Teaser__links .SP-Link.SP-Iconized--left"
            )
            if ical_link_element:
                ical_link = urllib.parse.urljoin(url, ical_link_element["href"])
                ical_link = urllib.parse.unquote(ical_link)
                ical_response = requests.get(ical_link)
                ical_data = ical_response.text
                cal = ics.Calendar(ical_data)
                event = list(cal.events)[0]

                event_title = event.name
                event_start = event.begin
                event_end = event.end
                event_location = event.location
                event_description = event.description
                event_url = event.url

                event_categories = event.categories
                tags_str = ", ".join(event_categories)

                germany_tz = pytz.timezone("Europe/Berlin")
                event_start = event_start.astimezone(germany_tz)
                event_end = event_end.astimezone(germany_tz)

                event_start_time = event_start.strftime("%H:%M Uhr")
                event_end_time = event_end.strftime("%H:%M Uhr")
                event_date = event_start.strftime("%a, %d %b %Y")

                event_html = f"""
                <div>"""

                if event_url:
                    webpage_response = requests.get(event_url)
                    webpage_soup = BeautifulSoup(
                        webpage_response.content, "html.parser"
                    )
                    picture_tag = webpage_soup.select_one("picture")
                    if picture_tag:
                        img_tag = picture_tag.find("img")
                        if img_tag:
                            image_url = urllib.parse.urljoin(
                                event_url, img_tag.get("src")
                            )
                            php_file_name = os.path.basename(event_url)
                            php_file_name = os.path.splitext(php_file_name)[0]
                            if php_file_name in image_url:
                                event_html += (
                                    f"<img src='{image_url}' alt='{event_title}'>"
                                )
                    else:
                        image_url = "https://www.stuttgart.de/openGraph-200x200.png"

                event_html = f"""
                    <div style="display: flex;">
                    <div style="flex-shrink: 0; margin-right: 10px;">
                    <a href='{event_url}' target='_blank' style='float: left; margin-right: 10px;'><img src='{image_url}' alt='{event_title}' style='max-width: 200px;'></a>
                    </div>
                    <div>
                    <p>{event_description}</p>
                    <p><a href='{ical_link}' target='_blank'>{event_start_time} - {event_end_time}, {event_date} &#128197;</a></p>"""

                if event_location:
                    google_maps_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(event_location)}"
                    event_html += f"<p><a href='{google_maps_link}' target='_blank'>{event_location}</a></p>"

                entrance_fee_element = webpage_soup.select_one(
                    ".SP-CallToAction__text .SP-Paragraph p"
                )
                if entrance_fee_element and entrance_fee_element.contents:
                    entrance_fee = entrance_fee_element.contents[0].strip()
                    event_html += f"<p>{entrance_fee}</p>"

                if event_url:
                    extended_description_elements = webpage_soup.select(
                        ".SP-ArticleContent .SP-Text:not(.SP-Text--notice) .SP-Paragraph p:not(.SP-CallToAction__text .SP-Paragraph p)"
                    )

                    for element in extended_description_elements:
                        br_tags = element.find_all("br")
                        for br_tag in br_tags:
                            br_tag.replace_with("\n")

                    extended_description = "\n".join(
                        [
                            element.text.strip()
                            for element in extended_description_elements
                        ]
                    )

                    if extended_description:
                        event_html += f"<p>{extended_description}</p>"

                if tags_str:
                    event_html += f"<p><strong>Tags:</strong> {tags_str}</p>"

                event_kicker_addon = event_entry.select_one(".SP-Kicker__addOn")
                if event_kicker_addon:
                    event_kicker_addon = event_kicker_addon.text.strip()
                    event_html += f"<p><strong>Zusätzliche Info:</strong> {event_kicker_addon}</p>"

                if event_url:
                    event_html += f"<p><a href='{event_url}' target='_blank'>{event_title} (link auf stuttgart.de)</a></p>"

                event_html += "</div>"

                event_exists = False
                for existing_item in channel.findall("item"):
                    existing_title_element = existing_item.find("title")
                    if existing_title_element is None:
                        continue

                    existing_title = existing_title_element.text
                    existing_pub_date = existing_item.find("pubDate").text
                    pub_date = formatdate(dt.timestamp(event_start), usegmt=True)

                    if existing_title == event_title and existing_pub_date == pub_date:
                        event_exists = True
                        logger.info(
                            f"Skipping duplicate event: {event_title}, date: {date}"
                        )
                        break

                if event_exists:
                    continue

                item = ET.SubElement(channel, "item")
                # Add the event to the XML file
                ET.SubElement(item, "title").text = event_title
                ET.SubElement(item, "description").text = html.unescape(event_html)
                ET.SubElement(item, "link").text = event_url
                pub_date = formatdate(dt.timestamp(event_start), usegmt=True)
                ET.SubElement(item, "pubDate").text = pub_date
                logger.info(f"Added to xml file: {event_title}, date: {date}")

    script_directory = os.path.dirname(os.path.abspath(__file__))
    rss_path = os.path.join(script_directory, rss_name)

    xml_data = ET.tostring(rss, encoding="utf-8")
    with open(rss_path, "wb") as f:
        f.write(xml_data)

    tree = ET.parse(rss_path)
    tree.write(rss_path, encoding="utf-8", xml_declaration=True)

    logger.info(f"{count_events(rss_path)} events added.")
    logger.info(f"RSS feed '{rss_name}' in {rss_path} generated successfully!")


if __name__ == "__main__":
    destination_folder = "/home/pi/rss_feeds"

    logger.info(f"Starting scraping script. ##############")

    # rss_name = "buehne_veranstaltungen.rss"
    # rss_title = "Bühne - Stuttgart"
    # rss_category = 79078
    # generate_rss_feed(rss_name, rss_title, rss_category)

    rss_name = "philo_veranstaltungen.rss"
    rss_title = "Literatur, Philosophie und Geschichte - Stuttgart"
    rss_category = 77317
    generate_rss_feed(rss_name, rss_title, rss_category)

    # rss_name = "musik_veranstaltungen.rss"
    # rss_title = "Musik - Stuttgart"
    # rss_category = 79091
    # generate_rss_feed(rss_name, rss_title, rss_category)

    move_rss_log_files(destination_folder)
    update_nextcloud_news()
    logger.info(f"Stopping scraping script. ##############")
