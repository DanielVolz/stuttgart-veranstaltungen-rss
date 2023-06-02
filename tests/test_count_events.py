import unittest
import xml.etree.ElementTree as ET
from rss_downloader import count_events


class CountEventsTestCase(unittest.TestCase):
    def test_count_events(self):
        # Create a sample XML file with events
        xml_content = """
        <root>
            <item>Event 1</item>
            <item>Event 2</item>
            <item>Event 3</item>
        </root>
        """
        with open("sample.xml", "w") as file:
            file.write(xml_content)

        # Call the count_events function
        event_count = count_events("sample.xml")

        # Assert that the count is correct
        self.assertEqual(event_count, 3)

        # Cleanup - delete the sample XML file
        import os

        os.remove("sample.xml")


if __name__ == "__main__":
    unittest.main()
