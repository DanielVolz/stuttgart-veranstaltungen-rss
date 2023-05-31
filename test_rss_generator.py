import unittest
from unittest.mock import patch
import os
import tempfile
import datetime
from xml.etree import ElementTree as ET
import subprocess
import json

from rss_downloader import update_nextcloud_news, count_events, move_rss_log_files, generate_rss_feed



class TestRSSGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.destination_folder = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_count_events(self):
        xml_file = "test_events.xml"

        # Create a sample XML file with 3 event entries
        root = ET.Element("root")
        for i in range(3):
            item = ET.SubElement(root, "item")
            ET.SubElement(item, "title").text = f"Event {i+1}"
        tree = ET.ElementTree(root)
        tree.write(xml_file)

        event_count = count_events(xml_file)
        self.assertEqual(event_count, 3)

        os.remove(xml_file)

    def test_update_nextcloud_news(self):
        with patch("subprocess.check_output") as mock_check_output:
            # Mock the subprocess.check_output call and return a sample JSON output
            sample_json = '[{"id": "1", "url": "https://rss.danielvolz.org/abc"}]'
            mock_check_output.return_value = sample_json

            with patch("subprocess.Popen"):
                update_nextcloud_news()

        mock_check_output.assert_called_once_with(
            ["sudo", "docker", "exec", "--user", "www-data", "-it", "nextcloud-aio-nextcloud", "php", "occ", "news:feed:list", "danielvolz"]
        )

        subprocess.Popen.assert_called_with(
            "sudo docker exec --user www-data -it nextcloud-aio-nextcloud php occ news:updater:update-feed danielvolz 1",
            shell=True
        )

    def test_move_rss_log_files(self):
        # Create temporary RSS and log files
        rss_file = "test.rss"
        log_file = "test.log"
        rss_path = os.path.join(self.destination_folder, rss_file)
        log_path = os.path.join(self.destination_folder, log_file)
        with open(rss_path, "w") as rss, open(log_path, "w") as log:
            rss.write("Sample RSS file")
            log.write("Sample log file")

        # Call the move_rss_log_files function
        move_rss_log_files(self.destination_folder)

        # Verify that the files are moved
        self.assertFalse(os.path.exists(rss_path))
        self.assertFalse(os.path.exists(log_path))

        moved_rss_path = os.path.join(self.destination_folder, rss_file)
        moved_log_path = os.path.join(self.destination_folder, log_file)
        self.assertTrue(os.path.exists(moved_rss_path))
        self.assertTrue(os.path.exists(moved_log_path))

    @patch("requests.get")
    def test_generate_rss_feed(self, mock_requests_get):
        rss_name = "test.rss"
        rss_title = "Test Category"
        rss_category = 12345

        # Create a sample response for the category page
        sample_response = """
            <html>
            <body>
                <article class="SP-Teaser SP-Grid__full SP-Teaser--event SP-Teaser--hasLinks SP-Teaser--textual">
                    <a class="SP-Link SP-Iconized--left" href="/event1.ics"></a>
                    <div class="SP-Teaser__links"></div>
                </article>
                <article class="SP-Teaser SP-Grid__full SP-Teaser--event SP-Teaser--hasLinks SP-Teaser--textual">
                    <a class="SP-Link SP-Iconized--left" href="/event2.ics"></a>
                    <div class="SP-Teaser__links"></div>
                </article>
            </body>
            </html>
        """
        mock_response = mock_requests_get.return_value
        mock_response.content = sample_response

        # Mock the response for each event page
        mock_event1_response = mock_requests_get.return_value
        mock_event1_response.content = "Event 1 Description"
        mock_event2_response = mock_requests_get.return_value
        mock_event2_response.content = "Event 2 Description"

        # Mock the current date
        current_date = datetime.datetime(2023, 5, 27)
        mock_datetime = self.create_mock_datetime(current_date)

        # Call the generate_rss_feed function
        generate_rss_feed(rss_name, rss_title, rss_category)

        # Verify that the RSS file is generated
        rss_path = os.path.join(os.getcwd(), rss_name)
        self.assertTrue(os.path.exists(rss_path))

        # Verify the contents of the RSS file
        with open(rss_path, "r") as rss_file:
            rss_content = rss_file.read()

        self.assertIn("<title>Event 1</title>", rss_content)
        self.assertIn("<description>Event 1 Description</description>", rss_content)
        self.assertIn("<link>https://rss.danielvolz.org/event1.ics</link>", rss_content)
        self.assertIn("<pubDate>Fri, 27 May 2023 00:00:00 +0000</pubDate>", rss_content)

        self.assertIn("<title>Event 2</title>", rss_content)
        self.assertIn("<description>Event 2 Description</description>", rss_content)
        self.assertIn("<link>https://rss.danielvolz.org/event2.ics</link>", rss_content)
        self.assertIn("<pubDate>Fri, 27 May 2023 00:00:00 +0000</pubDate>", rss_content)

    def create_mock_datetime(self, current_date):
        class MockDateTime(datetime.datetime):
            @classmethod
            def now(cls):
                return current_date

        return patch("datetime.datetime", MockDateTime)


if __name__ == "__main__":
    unittest.main()
