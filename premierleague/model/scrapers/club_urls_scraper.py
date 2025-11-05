import logging
from bs4 import BeautifulSoup
from .request_handler import RequestHandler
from .interfaces.club_urls_scraper import IClubUrlsScraper
from .premierleague_website_scraper import PremierleagueWebsiteScraper
from log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(RequestHandler)) 

class ClubUrlsScraper(PremierleagueWebsiteScraper, IClubUrlsScraper):
    def __init__(self, url=None):
        super().__init__()
        self._base_url = url if url else self._website_url + '/clubs?se=578'
        logger.debug(
            f"ClubUrlsScraper initialized with base URL: {self._base_url}",
            extra={"tags": ["init", "club_urls_scraper"]}
        )

    async def initialize(self):
        logger.info(
            "Initializing ClubUrlsScraper with RequestHandler",
            extra={"tags": ["init", "request_handler", "club_urls_scraper"]}
        )

        try:
            self._request_handler = RequestHandler()
            await self._request_handler.configure()
            logger.debug(
                "RequestHandler configured successfully",
                extra={"tags": ["request_handler", "configure", "club_urls_scraper"]}
            )

            structure = await self._request_handler.get(self._base_url)
            self._structure = BeautifulSoup(structure, 'html.parser')
            logger.info(
                f"Successfully fetched and parsed club list page: {self._base_url}",
                extra={"tags": ["html_parsing", "club_urls_scraper", "page_fetch"]}
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize ClubUrlsScraper: {str(e)}",
                exc_info=True,
                extra={"tags": ["init", "error", "club_urls_scraper"], "error": str(e)}
            )
            raise

    async def get_club_urls(self):
        logger.info(
            "Extracting club URLs from page structure",
            extra={"tags": ["data_extraction", "club_urls_scraper"]}
        )

        try:
            clubs = self._structure.select('.club-cards-wrapper .club-list .club-card-wrapper a')
            logger.debug(
                f"Found {len(clubs)} clubs in the HTML structure",
                extra={"tags": ["data_extraction", "club_count", "club_urls_scraper"]}
            )

            result = []
            logger.debug(
                "Header row added to result list",
                extra={"tags": ["data_structure", "club_urls_scraper"]}
            )

            for i, club in enumerate(clubs, start=1):
                try:
                    club_name = club.select_one('.club-card__info .club-card__name-container h2').get_text(strip=True)
                    club_page_url = str(self._website_url + club.get('href'))
                    result.append({"club_name": club_name, "club_page_url": club_page_url})
                    logger.debug(
                        f"Extracted club {i}: {club_name} - {club_page_url}",
                        extra={"tags": ["club_data", "club_urls_scraper"]}
                    )
                except Exception as inner_e:
                    logger.warning(
                        f"Failed to extract club info at index {i}: {str(inner_e)}",
                        exc_info=True,
                        extra={"tags": ["club_data", "warning", "club_urls_scraper"], "error": str(inner_e)}
                    )

            logger.info(
                f"Club URL extraction completed with {len(result) - 1} entries",
                extra={"tags": ["success", "club_urls_scraper", "data_extraction"]}
            )
            return result
        except Exception as e:
            logger.error(
                f"Unexpected error while extracting club URLs: {str(e)}",
                exc_info=True,
                extra={"tags": ["error", "club_urls_scraper", "data_extraction"], "error": str(e)}
            )
            raise
