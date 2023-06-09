import json
import shlex
import subprocess
import sys
from typing import Any, Dict, List

from rss_downloader import helpers

logger = helpers.setup_logging()

DOCKER_VERSION_COMMAND = ["docker", "--version"]
DOCKER_PS_COMMAND_FORMAT = "docker ps --filter name={} --format '{{{{.Names}}}}'"


def update_nextcloud_news(
    nextcloud_user_id: str,
    tld_rss_feed: str,
    nextcloud_container_name: str,
    enable_update: bool,
) -> None:
    """
    Update Nextcloud News feeds for a specific user.

    Parameters:
        - nextcloud_user_id (str): The ID of the Nextcloud user.
        - tld_rss_feed (str): The top-level domain of the RSS feed.
        - nextcloud_container_name (str): The name of the Nextcloud Docker container.
        - enable_update (bool): Flag indicating whether Nextcloud News feed(s) update is enabled.

    Returns:
        None
    """

    # Check if a settings variable is not set or empty.
    if not validate_input(
        nextcloud_user_id, tld_rss_feed, nextcloud_container_name, enable_update
    ):
        return

    # Check if the specified Nextcloud container is running
    container = get_running_containers(nextcloud_container_name)
    if not container:
        logger.error(f"Container '{nextcloud_container_name}' is not running.")
        return

    logger.info(f"Container '{nextcloud_container_name}' is running.")

    nextcloud_news_feeds = get_feed_list(nextcloud_user_id, nextcloud_container_name)
    nextcloud_news_feed_ids = filter_feed_ids_by_tld(nextcloud_news_feeds, tld_rss_feed)

    if not nextcloud_news_feed_ids:
        logger.info(
            f"No feeds starting with '{tld_rss_feed}' to update in Nextcloud News."
        )
        return

    update_feeds(nextcloud_user_id, nextcloud_container_name, nextcloud_news_feed_ids)


def get_running_containers(container_name: str) -> bool:
    """
    Check if a Docker container is running.

    Parameters:
        container_name (str): The name of the Docker container.

    Returns:
        bool: True if the specified container is running, False otherwise.
    """
    try:
        # Check if Docker is installed
        subprocess.run(DOCKER_VERSION_COMMAND, check=True, capture_output=True)
    except FileNotFoundError:
        logger.error("Docker is not installed on this host. Exiting.")
        sys.exit(1)

    command = DOCKER_PS_COMMAND_FORMAT.format(shlex.quote(container_name))
    nextcloud_container = subprocess.check_output(shlex.split(command), text=True)

    return container_name in nextcloud_container


def execute_shell_command(command: str) -> None:
    """
    Execute a shell command.

    Parameters:
        command (str): The shell command to execute.

    Returns:
        None

    Raises:
        None
    """

    with subprocess.Popen(shlex.split(command)) as process:
        process.communicate()

        if process.returncode == 0:
            logger.info(f"Command '{command}' executed successfully.")
        else:
            logger.error(f"Command '{command}' failed to execute.")


def validate_input(
    nextcloud_user_id: str,
    tld_rss_feed: str,
    nextcloud_container_name: str,
    enable_update: bool,
) -> bool:
    """
    Validate the input parameters for the update_nextcloud_news function.

    Parameters:
        nextcloud_user_id (str): The ID of the Nextcloud user.
        tld_rss_feed (str): The top-level domain of the RSS feed.
        nextcloud_container_name (str): The name of the Nextcloud Docker container.
        enable_update (bool): Flag indicating whether Nextcloud News feed(s) update is enabled.

    Returns:
        bool: True if all input parameters are valid, False otherwise.
    """
    if not enable_update:
        logger.info("Update of Nextcloud News is disabled.")
        return False

    if not nextcloud_user_id:
        logger.error("nextcloud_user_id is not set or empty.")
        return False

    if not tld_rss_feed:
        logger.error("tld_rss_feed is not set or empty.")
        return False

    if not nextcloud_container_name:
        logger.error("nextcloud_container_name is not set or empty.")
        return False

    return True


def get_feed_list(
    nextcloud_user_id: str, nextcloud_container_name: str
) -> List[Dict[str, Any]]:
    """
    Get the list of RSS feeds for the specified Nextcloud user.

    Parameters:
        nextcloud_user_id (str): The ID of the Nextcloud user.
        nextcloud_container_name (str): The name of the Nextcloud Docker container.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the feed information.
    """
    feed_list = subprocess.check_output(
        [
            "docker",
            "exec",
            "--user",
            "www-data",
            nextcloud_container_name,
            "php",
            "occ",
            "news:feed:list",
            nextcloud_user_id,
        ]
    )
    return json.loads(feed_list)


def filter_feed_ids_by_tld(
    nextcloud_news_feeds: List[Dict[str, Any]], tld_rss_feed: str
) -> List[int]:
    """
    Extract the feed IDs from the given Nextcloud news feeds that match the specified top-level domain.

    Parameters:
        nextcloud_news_feeds (List[Dict[str, Any]]): A list of Nextcloud news feeds.
        tld_rss_feed (str): The top-level domain of the RSS feed.

    Returns:
        List[int]: A list of feed IDs matching the specified top-level domain.
    """
    return [
        nextcloud_news_feed["id"]
        for nextcloud_news_feed in nextcloud_news_feeds
        if nextcloud_news_feed["url"].startswith(tld_rss_feed)
    ]


def update_feeds(
    nextcloud_user_id: str,
    nextcloud_container_name: str,
    nextcloud_news_feed_ids: List[int],
) -> None:
    """
    Mark as read and update Nextcloud News feeds for the specified user.

    Parameters:
        nextcloud_user_id (str): The ID of the Nextcloud user.
        nextcloud_container_name (str): The name of the Nextcloud Docker container.
        nextcloud_news_feed_ids (List[int]): A list of feed IDs to update.

    Returns:
        None
    """
    logger.info("Begin updating Nextcloud News feeds.")
    for nextcloud_news_feed_id in nextcloud_news_feed_ids:
        commands = [
            (
                f"docker exec --user www-data {nextcloud_container_name} php"
                f" occ news:feed:read {nextcloud_user_id} {nextcloud_news_feed_id}"
            ),
            (
                f"docker exec --user www-data {nextcloud_container_name} php"
                " occ news:updater:update-feed"
                f" {nextcloud_user_id} {nextcloud_news_feed_id}"
            ),
        ]
        for command in commands:
            execute_shell_command(command)
