import unittest
from unittest.mock import patch, Mock
from subprocess import CompletedProcess

from rss_downloader import update_nextcloud_news


class UpdateNextcloudNewsTestCase(unittest.TestCase):

    @patch('subprocess.run')
    @patch('rss_downloader.logger')
    def test_update_nextcloud_news(self, mock_logger, mock_run):
        # Create a mock logger object
        logger_mock = Mock()
        mock_logger.getLogger.return_value = logger_mock

        # Mock the subprocess.run() function to return successful and unsuccessful commands
        mock_run.side_effect = [
            CompletedProcess(args=[], returncode=0),  # Successful command
            CompletedProcess(args=[], returncode=1),  # Unsuccessful command
        ]

        # Call the function under test
        update_nextcloud_news()

        # Assert that the commands were executed and logged correctly
        expected_calls = [
            'sudo docker exec --user www-data nextcloud-aio-nextcloud php occ news:feed:read danielvolz <feed_id>',
            'sudo docker exec --user www-data nextcloud-aio-nextcloud php occ news:updater:update-feed danielvolz <feed_id>',
        ]

        # Assert the expected calls were made
        actual_calls = [call[0][0] for call in mock_run.call_args_list]
        self.assertListEqual(expected_calls, actual_calls)

        # Assert that the correct logs were made for each command
        expected_logs = [
            f"Command '{expected_calls[0]}' executed successfully.",
            f"Command '{expected_calls[1]}' encountered an error with return code 1.",
        ]
        actual_logs = [log[0][0] for log in logger_mock.method_calls if log[0] == 'info' or log[0] == 'error']
        self.assertListEqual(expected_logs, actual_logs)


if __name__ == '__main__':
    unittest.main()
