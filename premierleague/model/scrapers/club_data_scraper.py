from bs4 import BeautifulSoup
import re
import sys
from .utils import UrlValidator
from .request_handler import RequestHandler
from .interfaces.club_data_scraper import IClubDataScraper
from .premierleague_website_scraper import PremierleagueWebsiteScraper
import logging
from premierleague.log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(UrlValidator))
configure_logger(resolve_class_module_name(RequestHandler))

class ClubDataScraper(PremierleagueWebsiteScraper, IClubDataScraper):
    def __init__(self, url):
        logger.debug("Initializing ClubDataScraper with URL: %s", url, extra={"tags": ["init", "input"]})
        if not UrlValidator.validate_club_page_url(url):
            logger.error("Invalid club page URL provided: %s", url, extra={"error": "InvalidClubURL", "tags": ["init", "validation"]})
            raise ValueError("the url provided isn't valid")

        super().__init__()
        self._base_url = url
        self.club_data = {
            'club_name': str(),
            'establishment_year': str(),
            'manager_name': str(),
            'city': str(),
            'stadium': str(),
            'logo': bytes(),
            'squad_page_url': str()
        }
        self._initialized = False
        logger.info("ClubDataScraper instance created successfully.", extra={"tags": ["init", "success"]})

    async def initialize(self):
        logger.debug("Initializing scraper with base URL: %s", self._base_url, extra={"tags": ["init", "network"]})
        try:
            main_page_url = self._base_url
            directory_page_url = self._base_url.replace('overview', 'directory')

            self._request_handler = RequestHandler()
            await self._request_handler.configure()
            logger.info("RequestHandler configured.", extra={"tags": ["request", "setup"]})

            main_page_structure = await self._request_handler.get(main_page_url)
            logger.info("Fetched main page HTML.", extra={"tags": ["request", "html"]})

            directory_page_structure = await self._request_handler.get(directory_page_url)
            logger.info("Fetched directory page HTML.", extra={"tags": ["request", "html"]})

            self._structures = {
                'main_page': BeautifulSoup(main_page_structure, 'html.parser'),
                'directory_page': BeautifulSoup(directory_page_structure, 'html.parser')
            }

            self._initialized = True
            logger.info("Scraper initialized successfully.", extra={"tags": ["init", "success"]})
        except Exception as e:
            logger.error("Initialization failed: %s", str(e), extra={"error": str(e), "tags": ["init", "exception"]})
            raise

    async def get_all_data(self) -> dict:
        logger.debug("Fetching all club data.", extra={"tags": ["data", "get_all"]})
        self._raise_if_not_initialized()

        try:
            self.club_data['club_name'] = await self.get_club_name()
            self.club_data['establishment_year'] = await self.get_establishment_year()
            self.club_data['manager_name'] = await self.get_manager_name()
            # self.club_data['city'] = await self.get_city_name()
            self.club_data['stadium'] = await self.get_stadium_name()
            self.club_data['logo'] = await self.get_club_logo()
            self.club_data['squad_page_url'] = await self.get_squad_page_url()

            logger.info("All club data fetched successfully.", extra={"tags": ["data", "complete"]})
            return self.club_data
        except Exception as e:
            logger.critical("Failed to fetch all club data: %s", str(e), extra={"error": str(e), "tags": ["data", "error"]})
            raise

    async def get_club_name(self):
        self._raise_if_not_initialized()

        if self.club_data['club_name']:
            logger.debug("Club name already cached.", extra={"tags": ["cache", "club_name"]})
            return self.club_data['club_name']

        try:
            name = self._structures['main_page'].select_one('h1.club-profile-header__title').get_text(strip=True)
            self.club_data['club_name'] = name
            logger.info("Club name extracted: %s", name, extra={"tags": ["extract", "club_name"]})
            return name
        except Exception as e:
            logger.error("Error extracting club name: %s", str(e), extra={"error": str(e), "tags": ["extract", "club_name"]})
            raise

    async def get_establishment_year(self):
        self._raise_if_not_initialized()

        if self.club_data['establishment_year']:
            logger.debug("Establishment year already cached.", extra={"tags": ["cache", "establishment_year"]})
            return self.club_data['establishment_year']

        try:
            element = self._structures['main_page'].select_one('.club-profile-bio__metadata-item.club-profile-bio__metadata-item--established p')
            year = re.search(r'\d+', element.get_text(strip=True)).group()
            self.club_data['establishment_year'] = year
            logger.info("Establishment year extracted: %s", year, extra={"tags": ["extract", "establishment_year"]})
            return year
        except Exception as e:
            logger.error("Error extracting establishment year: %s", str(e), extra={"error": str(e), "tags": ["extract", "establishment_year"]})
            raise

    async def get_manager_name(self):
        self._raise_if_not_initialized()

        if self.club_data['manager_name']:
            logger.debug("Manager name already cached.", extra={"tags": ["cache", "manager_name"]})
            return self.club_data['manager_name']

        try:
            pattern = re.compile(r'^Head Coach$|^First-team Manager$|^Manager$', re.IGNORECASE)
            title_element = self._structures['directory_page'].find(string=pattern)
            manager = title_element.parent.parent.parent.parent.select_one('.cardBody').get_text(strip=True)
            self.club_data['manager_name'] = manager
            logger.info("Manager name extracted: %s", manager, extra={"tags": ["extract", "manager_name"]})
            return manager
        except Exception as e:
            logger.error("Error extracting manager name: %s", str(e), extra={"error": str(e), "tags": ["extract", "manager_name"]})
            raise

    async def get_city_name(self):
        self._raise_if_not_initialized()

        if self.club_data['city']:
            logger.debug("City name already cached.", extra={"tags": ["cache", "city"]})
            return self.club_data['city']

        try:
            city_text = self._structures['main_page'].select_one('span.club-header__club-stadium').text
            city = city_text.split(',')[1].strip()
            self.club_data['city'] = city
            logger.info("City extracted: %s", city, extra={"tags": ["extract", "city"]})
            return city
        except Exception as e:
            logger.error("Error extracting city name: %s", str(e), extra={"error": str(e), "tags": ["extract", "city"]})
            raise

    async def get_stadium_name(self):
        self._raise_if_not_initialized()

        if self.club_data['stadium']:
            logger.debug("Stadium name already cached.", extra={"tags": ["cache", "stadium"]})
            return self.club_data['stadium']

        try:
            stadium_text = self._structures['main_page'].select_one('span.club-header__club-stadium').text
            stadium = stadium_text.split(',')[0].strip()
            self.club_data['stadium'] = stadium
            logger.info("Stadium extracted: %s", stadium, extra={"tags": ["extract", "stadium"]})
            return stadium
        except Exception as e:
            logger.error("Error extracting stadium name: %s", str(e), extra={"error": str(e), "tags": ["extract", "stadium"]})
            raise

    async def get_club_logo(self):
        self._raise_if_not_initialized()

        if self.club_data['logo']:
            logger.debug("Club logo already cached.", extra={"tags": ["cache", "logo"]})
            return self.club_data['logo']

        try:
            logo_url = self._structures['main_page'].select_one('.club-header__content img.club-header__badge')['src']
            logo_data = await self._request_handler.get(logo_url, raw=True)
            self.club_data['logo'] = logo_data
            logger.info("Club logo downloaded from URL: %s", logo_url, extra={"tags": ["download", "logo"]})
            return logo_data
        except Exception as e:
            logger.error("Error downloading club logo: %s", str(e), extra={"error": str(e), "tags": ["download", "logo"]})
            raise

    async def get_squad_page_url(self):
        self._raise_if_not_initialized()

        if self.club_data['squad_page_url']:
            logger.debug("Squad page URL already cached.", extra={"tags": ["cache", "squad_page_url"]})
            return self.club_data['squad_page_url']

        try:
            relative_url = self._structures['main_page'].select_one('.tab.club-navigation__tab:nth-child(2) a')['href']
            full_url = self._base_url.replace('overview', relative_url)
            self.club_data['squad_page_url'] = full_url
            logger.info("Squad page URL extracted: %s", full_url, extra={"tags": ["extract", "squad_page_url"]})
            return full_url
        except Exception as e:
            logger.error("Error extracting squad page URL: %s", str(e), extra={"error": str(e), "tags": ["extract", "squad_page_url"]})
            raise

    def _raise_if_not_initialized(self):
        if not self._initialized:
            logger.critical("Scraper used before initialization.", extra={"error": "NotInitialized", "tags": ["init", "misuse"]})
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")
