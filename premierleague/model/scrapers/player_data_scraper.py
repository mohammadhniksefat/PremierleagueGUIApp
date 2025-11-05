import logging
import re
from bs4 import BeautifulSoup
from .interfaces.player_data_scraper import IPlayerDataScraper
from .utils import UrlValidator
from .request_handler import RequestHandler
from .premierleague_website_scraper import PremierleagueWebsiteScraper
from log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(RequestHandler))
configure_logger(resolve_class_module_name(UrlValidator))

class PlayerDataScraper(PremierleagueWebsiteScraper, IPlayerDataScraper):
    def __init__(self, url):
        logger.debug("Initializing PlayerDataScraper", extra={"tags": ["init", "player_scraper"], "url": url})
        if not UrlValidator.validate_player_page_url(url):
            logger.error("Invalid player page URL", extra={"tags": ["init", "validation"], "error": "Invalid player URL", "url": url})
            raise ValueError("the url provided isn't valid")

        super().__init__()
        self._base_url = url
        self._initialized = False
        self.player_data = {
            'firstname': str(),
            'lastname': str(),
            'club_name': str(),
            'position': str(),
            'nationality': str(),
            'date_of_birth': str(),
            'shirt_number': str(),
            'age': int(),
            'height': int(),
            'picture': bytes()
        }
        logger.info("PlayerDataScraper initialized", extra={"tags": ["init", "player_scraper"]})

    async def initialize(self) -> None:
        logger.info("Initializing request handler and scraping structure", extra={"tags": ["init", "request_handler"]})
        self._request_handler = RequestHandler()
        try:
            await self._request_handler.configure()
            structure = await self._request_handler.get(self._base_url)
            self._structures = {
                'main': BeautifulSoup(structure, 'html.parser')
            }
            self._initialized = True
            logger.info("Initialization completed", extra={"tags": ["init", "player_scraper"]})
        except Exception as e:
            logger.critical("Failed during scraper initialization", exc_info=True,
                            extra={"tags": ["init", "error"], "error": str(e)})
            raise

    async def get_all_data(self) -> dict:
        self._raise_if_not_initialized()
        logger.info("Starting to scrape all player data", extra={"tags": ["scrape", "all_data"]})

        try:
            self.player_data = {
                'firstname': await self.get_firstname(),
                'lastname': await self.get_lastname(),
                'club_name': await self.get_club_name(),
                'position': await self.get_position(),
                'nationality': await self.get_nationality(),
                'date_of_birth': await self.get_date_of_birth(),
                'shirt_number': await self.get_shirt_number(),
                'age': await self.get_age(),
                'height': await self.get_height(),
                'picture': await self.get_picture()
            }
            logger.info("All player data scraped successfully", extra={"tags": ["scrape", "all_data"]})
        except Exception as e:
            logger.error("Error while scraping all data", exc_info=True,
                         extra={"tags": ["scrape", "all_data"], "error": str(e)})
            raise

        return self.player_data

    async def get_club_name(self):
        self._raise_if_not_initialized()
        if self.player_data['club_name']:
            return self.player_data['club_name']

        try:
            selector = '.playerSidebar .player-overview__side-widget:first-child .player-overview__col .player-overview__info a'
            club_name = self._structures['main'].select_one(selector)
            self.player_data['club_name'] = club_name.get_text(strip=True)
            logger.debug("Extracted club name", extra={"tags": ["scrape", "club_name"], "value": self.player_data['club_name']})
            return self.player_data['club_name']
        except Exception as e:
            logger.error("Failed to extract club name", exc_info=True,
                         extra={"tags": ["scrape", "club_name"], "error": str(e)})
            raise

    async def get_firstname(self):
        self._raise_if_not_initialized()
        if self.player_data['firstname']:
            return self.player_data['firstname']

        try:
            self.player_data['firstname'] = self._structures['main'].select_one('.player-header__name-first').get_text(strip=True)
            logger.debug("Extracted firstname", extra={"tags": ["scrape", "firstname"], "value": self.player_data['firstname']})
            return self.player_data['firstname']
        except Exception as e:
            logger.error("Failed to extract firstname", exc_info=True,
                         extra={"tags": ["scrape", "firstname"], "error": str(e)})
            raise

    async def get_lastname(self):
        self._raise_if_not_initialized()
        if self.player_data['lastname']:
            return self.player_data['lastname']

        try:
            self.player_data['lastname'] = self._structures['main'].select_one('.player-header__name-last').get_text(strip=True)
            logger.debug("Extracted lastname", extra={"tags": ["scrape", "lastname"], "value": self.player_data['lastname']})
            return self.player_data['lastname']
        except Exception as e:
            logger.error("Failed to extract lastname", exc_info=True,
                         extra={"tags": ["scrape", "lastname"], "error": str(e)})
            raise

    async def get_position(self):
        self._raise_if_not_initialized()
        if self.player_data['position']:
            return self.player_data['position']

        try:
            selector = '.playerSidebar .player-overview.u-hide-mob .player-overview__side-widget:first-child > .player-overview__col:nth-child(3) .player-overview__info'
            self.player_data['position'] = self._structures['main'].select_one(selector).get_text(strip=True)
            logger.debug("Extracted position", extra={"tags": ["scrape", "position"], "value": self.player_data['position']})
            return self.player_data['position']
        except Exception as e:
            logger.error("Failed to extract position", exc_info=True,
                         extra={"tags": ["scrape", "position"], "error": str(e)})
            raise

    async def get_nationality(self):
        self._raise_if_not_initialized()
        if self.player_data['nationality']:
            return self.player_data['nationality']

        try:
            self.player_data['nationality'] = self._structures['main'].select_one('.player-info__player-country').get_text(strip=True)
            logger.debug("Extracted nationality", extra={"tags": ["scrape", "nationality"], "value": self.player_data['nationality']})
            return self.player_data['nationality']
        except Exception as e:
            logger.error("Failed to extract nationality", exc_info=True,
                         extra={"tags": ["scrape", "nationality"], "error": str(e)})
            raise

    async def get_shirt_number(self):
        self._raise_if_not_initialized()
        if self.player_data['shirt_number']:
            return self.player_data['shirt_number']

        try:
            self.player_data['shirt_number'] = self._structures['main'].select_one('.player-header div.player-header__player-number').get_text(strip=True)
            logger.debug("Extracted shirt number", extra={"tags": ["scrape", "shirt_number"], "value": self.player_data['shirt_number']})
            return self.player_data['shirt_number']
        except Exception as e:
            logger.error("Failed to extract shirt number", exc_info=True,
                         extra={"tags": ["scrape", "shirt_number"], "error": str(e)})
            raise

    async def get_date_of_birth(self):
        self._raise_if_not_initialized()
        if self.player_data['date_of_birth']:
            return self.player_data['date_of_birth']

        try:
            dob_block = self._structures['main'].select_one('.player-info__details-list .player-info__col:nth-child(2) .player-info__info')
            dob_text = dob_block.get_text(strip=True).split('  ')[0]
            self.player_data['date_of_birth'] = dob_text
            logger.debug("Extracted date of birth", extra={"tags": ["scrape", "dob"], "value": dob_text})
            return dob_text
        except Exception as e:
            logger.error("Failed to extract date of birth", exc_info=True,
                         extra={"tags": ["scrape", "dob"], "error": str(e)})
            raise

    async def get_age(self):
        self._raise_if_not_initialized()
        if self.player_data['age']:
            return self.player_data['age']

        try:
            info_block = self._structures['main'].select_one('.player-info__details-list .player-info__col:nth-child(2) .player-info__info')
            age_text = info_block.get_text(strip=True).split('  ')[1]
            self.player_data['age'] = int(re.search(r'\d+', age_text).group())
            logger.debug("Extracted age", extra={"tags": ["scrape", "age"], "value": self.player_data['age']})
            return self.player_data['age']
        except Exception as e:
            logger.error("Failed to extract age", exc_info=True,
                         extra={"tags": ["scrape", "age"], "error": str(e)})
            raise

    async def get_height(self):
        self._raise_if_not_initialized()
        if self.player_data['height']:
            return self.player_data['height']

        try:
            height_string = self._structures['main'].select_one('.player-info__col:nth-child(3) .player-info__info').get_text(strip=True)
            self.player_data['height'] = int(re.match(r'\d+', height_string).group())
            logger.debug("Extracted height", extra={"tags": ["scrape", "height"], "value": self.player_data['height']})
            return self.player_data['height']
        except Exception as e:
            logger.error("Failed to extract height", exc_info=True,
                         extra={"tags": ["scrape", "height"], "error": str(e)})
            raise

    async def get_picture(self):
        self._raise_if_not_initialized()
        if self.player_data['picture']:
            return self.player_data['picture']

        try:
            picture_url = self._structures['main'].select_one('.imgContainer img.img')['src']
            logger.debug("Found picture URL", extra={"tags": ["scrape", "picture"], "url": picture_url})
            self.player_data['picture'] = await self._request_handler.get(url=picture_url, raw=True)
            logger.info("Fetched player image bytes", extra={"tags": ["scrape", "picture"]})
            return self.player_data['picture']
        except Exception as e:
            logger.error("Failed to extract or fetch player image", exc_info=True,
                         extra={"tags": ["scrape", "picture"], "error": str(e)})
            raise

    def _raise_if_not_initialized(self):
        if not self._initialized:
            logger.error("Scraper used before initialization", extra={"tags": ["error", "init"], "error": "scraper not initialized"})
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")
        logger.debug("Scraper is initialized", extra={"tags": ["check", "init"]})
