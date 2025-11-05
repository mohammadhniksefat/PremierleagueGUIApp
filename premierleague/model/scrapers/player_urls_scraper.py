import logging
from bs4 import BeautifulSoup
from .interfaces.player_urls_scraper import IPlayerUrlsScraper
from .utils import UrlValidator
from .request_handler import RequestHandler
from .club_urls_scraper import ClubUrlsScraper
from .premierleague_website_scraper import PremierleagueWebsiteScraper
from premierleague.log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(ClubUrlsScraper))
configure_logger(resolve_class_module_name(RequestHandler))
configure_logger(resolve_class_module_name(UrlValidator))

class PlayerUrlsScraper(PremierleagueWebsiteScraper, IPlayerUrlsScraper):
    def __init__(self, club_name=None, url=None):
        super().__init__()
        self._club_name = club_name
        self._url = url
        self._initialized = False
        logger.debug("PlayerUrlsScraper instance created", extra={"tags": ["init"]})

    async def initialize(self) -> None:
        logger.info("Initializing PlayerUrlsScraper...", extra={"tags": ["init"]})
        try:
            self._request_handler = RequestHandler()
            await self._request_handler.configure()
            logger.debug("RequestHandler configured", extra={"tags": ["request_handler"]})

            if self._url:
                logger.debug(f"URL provided: {self._url}", extra={"tags": ["input"]})
                if not UrlValidator.validate_squad_page_url(self._url):
                    logger.warning("Provided URL is not a squad page. Attempting to locate squad page...", extra={"tags": ["validation"]})
                    self._url = await self._scrap_squad_page_url(club_page_url=self._url)
            elif self._club_name:
                logger.debug(f"Club name provided: {self._club_name}", extra={"tags": ["input"]})
                self._url = await self._scrap_squad_page_url(club_name=self._club_name)
            else:
                logger.critical("Initialization failed: No identifier provided", extra={"tags": ["init", "error"], "error": "No URL or club_name provided"})
                raise ValueError("didn't provided any identifier")
            
            self.structure = await self._request_handler.get(self._url)
            self.structure = BeautifulSoup(self.structure, 'html.parser')

            self._initialized = True
            logger.info("PlayerUrlsScraper initialized successfully", extra={"tags": ["init"]})
        except Exception as e:
            logger.exception("Failed to initialize PlayerUrlsScraper", extra={"tags": ["init", "error"], "error": str(e)})
            raise

    async def get_club_player_urls(self) -> dict[str, str]:
        self._raise_if_not_initialized()
        logger.info("Fetching player URLs from club squad page", extra={"tags": ["player_urls"]})

        result = []
        columns_row = ("player_name", "player_page_url")
        result.append(columns_row)

        try:
            player_elements = self.structure.select('li.stats-card[data-widget="featured-player"] a.stats-card__wrapper')
            logger.debug(f"Found {len(player_elements)} player elements", extra={"tags": ["scraping"]})

            for index, player_element in enumerate(player_elements):
                firstname = player_element.select_one('.stats-card__player-first').get_text(strip=True)
                lastname = player_element.select_one('.stats-card__player-last').get_text(strip=True)
                full_name = firstname + lastname

                player_page_url = self._website_url + player_element.get('href')
                result.append({'player_name': full_name, 'player_page_url': player_page_url})
                logger.debug(f"Extracted player #{index + 1}: {full_name} -> {player_page_url}", extra={"tags": ["player_data"]})
            
            logger.info(f"Successfully extracted {len(player_elements)} players", extra={"tags": ["player_urls"]})
            return result
        except Exception as e:
            logger.exception("Failed to extract player URLs", extra={"tags": ["scraping", "error"], "error": str(e)})
            raise

    async def _scrap_squad_page_url(self, club_name=None, club_page_url=None):
        logger.debug("Attempting to scrap squad page URL", extra={"tags": ["squad_url"]})
        try:
            if club_page_url:
                logger.debug(f"Using provided club page URL: {club_page_url}", extra={"tags": ["squad_url"]})
            elif club_name:
                logger.debug(f"Looking up squad page from club name: {club_name}", extra={"tags": ["squad_url"]})
                scraper = ClubUrlsScraper()
                await scraper.initialize()
                club_urls = scraper.get_club_urls()

                if club_name not in club_urls:
                    logger.error(f"Club name '{club_name}' not found in club URLs", extra={"tags": ["squad_url", "error"], "error": "Club name not found"})
                    raise ValueError(f"Club name '{club_name}' not found")

                club_page_url = club_urls[club_name]
                logger.debug(f"Resolved club page URL: {club_page_url}", extra={"tags": ["squad_url"]})
                squad_page_url = await self._scrap_squad_page_url(club_page_url=club_page_url)
                return squad_page_url
            else:
                logger.critical("No argument provided for _scrap_squad_page_url", extra={"tags": ["squad_url", "error"], "error": "No club_name or club_page_url provided"})
                raise ValueError("didn't provided any argument")

            page_structure = await self._request_handler.get(club_page_url)
            page_structure = BeautifulSoup(page_structure, 'html.parser')
            squad_button = page_structure.select_one('ul.club-navigation__nav a.club-navigation__link[data-text="Squad"]')

            if not squad_button:
                logger.error("Squad button not found on club page", extra={"tags": ["squad_url", "error"], "error": "Squad button not found"})
                raise RuntimeError("Squad button not found")

            squad_page_url = squad_button.get('href')
            full_url = club_page_url.replace('overview', squad_page_url)
            logger.info(f"Squad page URL resolved: {full_url}", extra={"tags": ["squad_url"]})
            return full_url
        except Exception as e:
            logger.exception("Failed to scrap squad page URL", extra={"tags": ["squad_url", "error"], "error": str(e)})
            raise

    def _raise_if_not_initialized(self):
        if not self._initialized:
            logger.critical("Attempt to use scraper before initialization", extra={"tags": ["init", "error"], "error": "Scraper not initialized"})
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")