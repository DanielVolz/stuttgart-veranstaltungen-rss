from rss_downloader import docker_utils, helpers, rss_generation, rss_utils
from rss_downloader.config import settings


def main() -> None:
    """
    The main function of the script.

    Returns:
        None
    """
    logger = helpers.setup_logging()

    logger.info("## Starting scraping script. ##")

    rss_feeds = settings.get("rss_feeds")
    rss_generation.generate_rss_feed(rss_feeds)

    enable_move = settings.default.get("enable_move_rss")
    destination_folder = settings.default.get("destination_folder")
    rss_utils.move_rss_files(destination_folder, enable_move)

    enable_update = settings.default.get("enable_update_nextcloud_news")
    nextcloud_user_id = settings.default.get("nextcloud_user_id")
    tld_rss_feed = settings.default.get("rss_tld")
    nextcloud_container_name = settings.default.get("nextcloud_container_name")
    docker_utils.update_nextcloud_news(
        nextcloud_user_id, tld_rss_feed, nextcloud_container_name, enable_update
    )

    logger.info("## Stopping scraping script. ##")
