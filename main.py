from src.rss_downloader.config import settings
from src.rss_downloader.docker_utils import update_nextcloud_news
from src.rss_downloader.log_helper import setup_logging
from src.rss_downloader.rss_generation import generate_rss_feed
from src.rss_downloader.rss_utils import move_rss_files

logger = setup_logging()


logger.info("## Starting scraping script. ##")

rss_feeds = settings.get("rss_feeds")
generate_rss_feed(rss_feeds)

enable_move = settings.default.get("enable_move_rss")
destination_folder = settings.default.get("destination_folder")
move_rss_files(destination_folder, enable_move)

enable_update = settings.default.get("enable_update_nextcloud_news")
nextcloud_user_id = settings.default.get("nextcloud_user_id")
tld_rss_feed = settings.default.get("rss_tld")
nextcloud_container_name = settings.default.get("nextcloud_container_name")
update_nextcloud_news(
    nextcloud_user_id, tld_rss_feed, nextcloud_container_name, enable_update
)

logger.info("## Stopping scraping script. ##")
