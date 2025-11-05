import logging
import re
from .interfaces.match_data_scraper import IMatchDataScraper
from .utils import UrlValidator
from .request_handler import PlaywrightRequestHandler
from .premierleague_website_scraper import PremierleagueWebsiteScraper
from playwright.async_api import async_playwright
from log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(PlaywrightRequestHandler))
configure_logger(resolve_class_module_name(UrlValidator))

class MatchDataScraper(PremierleagueWebsiteScraper, IMatchDataScraper):
    def __init__(self, url):
        logger.debug("Initializing MatchDataScraper", extra={"tags": ["scraper", "init"]})
        if not UrlValidator.validate_match_page_url(url):
            logger.error("Invalid match page URL", extra={"tags": ["scraper", "validation"], "error": "InvalidMatchPageURL"})
            raise ValueError("The URL provided isn't valid")
        
        super().__init__()
        self._base_url = url
        self._initialized = False
        self.match_data = {
            'timestamp': int(),
            'round_number': int(),
            'referee_name': str(),
            'home_team_data': {
                'name': str(),
                'score': int()
            },
            'away_team_data': {
                'name': str(),
                'score': int()
            }
        }
        logger.info("MatchDataScraper initialized successfully", extra={"tags": ["scraper", "init"]})

    async def initialize(self) -> None:
        logger.debug("Initializing PlaywrightRequestHandler", extra={"tags": ["scraper", "init"]})
        self._request_handler = PlaywrightRequestHandler()
        await self._request_handler.configure()
        self._initialized = True
        logger.info("Scraper initialized and ready", extra={"tags": ["scraper", "init"]})

    async def get_all_data(self) -> dict:
        self._raise_if_not_initialized()
        logger.info("Starting full match data scraping", extra={"tags": ["scraper", "full"]})

        async def scraper(page):
            try:
                round_number = await page.locator('.mc-header__gameweek-selector-current-gameweek--long').first.text_content()
                self.match_data['round_number'] = int(re.search(r'\d+', round_number).group())

                self.match_data['timestamp'] = int(await page.locator('.mc-summary__info-kickoff .renderKOContainer').first.get_attribute('data-kickoff'))

                self.match_data['referee_name'] = await page.locator('.mc-summary__info:last-child').text_content().lstrip('Ref: ')

                home_team_page_url = await page.locator('.mc-summary__team-container:nth-child(1) a.mc-summary__badge-container').first.get_attribute('href')
                away_team_page_url = await page.locator('.mc-summary__team-container:nth-child(2) a.mc-summary__badge-container').first.get_attribute('href')

                match_result = await page.locator('.mc-summary__score').text_content()
                match_result = match_result.split(' - ')

                self.match_data['home_team_data']['score'] = int(match_result[0])
                self.match_data['away_team_data']['score'] = int(match_result[1])

                await self._request_handler.goto(page, home_team_page_url)
                self.match_data['home_team_data']['name'] = await page.locator('h2.club-header__team-name').text_content()

                await self._request_handler.goto(page, away_team_page_url)
                self.match_data['away_team_data']['name'] = await page.locator('h2.club-header__team-name').text_content()

                logger.info("Full match data scraped successfully", extra={"tags": ["scraper", "full"]})
                return self.match_data
            except Exception as e:
                logger.error("Failed to scrape full match data", extra={"tags": ["scraper", "full"], "error": str(e)})
                raise

        return await self._create_context_then_callback(scraper)

    async def get_timestamp(self) -> int:
        self._raise_if_not_initialized()
        if self.match_data['timestamp']:
            logger.debug("Returning cached timestamp", extra={"tags": ["scraper", "timestamp"]})
            return self.match_data['timestamp']

        async def scraper(page):
            try:
                logger.debug("Scraping timestamp...", extra={"tags": ["scraper", "timestamp"]})
                self.match_data['timestamp'] = int(await page.locator('.mc-summary__info-kickoff .renderKOContainer').first.get_attribute('data-kickoff'))
                logger.info("Timestamp scraped", extra={"tags": ["scraper", "timestamp"]})
                return self.match_data['timestamp']
            except Exception as e:
                logger.error("Failed to scrape timestamp", extra={"tags": ["scraper", "timestamp"], "error": str(e)})
                raise

        return await self._create_context_then_callback(scraper)

    async def get_round_number(self) -> int:
        self._raise_if_not_initialized()
        if self.match_data['round_number']:
            logger.debug("Returning cached round number", extra={"tags": ["scraper", "round"]})
            return self.match_data['round_number']

        async def scraper(page):
            try:
                logger.debug("Scraping round number...", extra={"tags": ["scraper", "round"]})
                string = await page.locator('.mc-header__gameweek-selector-current-gameweek--long').first.text_content()
                self.match_data['round_number'] = int(re.search(r'\d+', string).group())
                logger.info("Round number scraped", extra={"tags": ["scraper", "round"]})
                return self.match_data['round_number']
            except Exception as e:
                logger.error("Failed to scrape round number", extra={"tags": ["scraper", "round"], "error": str(e)})
                raise

        return await self._create_context_then_callback(scraper)

    async def get_referee_name(self) -> str:
        self._raise_if_not_initialized()
        if self.match_data['referee_name']:
            logger.debug("Returning cached referee name", extra={"tags": ["scraper", "referee"]})
            return self.match_data['referee_name']

        async def scraper(page):
            try:
                logger.debug("Scraping referee name...", extra={"tags": ["scraper", "referee"]})
                referee_name = await page.locator('.mc-summary__info:last-child').text_content()
                self.match_data['referee_name'] = referee_name.strip().lstrip('Ref: ')
                logger.info("Referee name scraped", extra={"tags": ["scraper", "referee"]})
                return self.match_data['referee_name']
            except Exception as e:
                logger.error("Failed to scrape referee name", extra={"tags": ["scraper", "referee"], "error": str(e)})
                raise

        return await self._create_context_then_callback(scraper)

    async def get_home_team_data(self) -> dict:
        self._raise_if_not_initialized()
        if self.match_data['home_team_data']['name'] and self.match_data['home_team_data']['score']:
            logger.debug("Returning cached home team data", extra={"tags": ["scraper", "home_team"]})
            return self.match_data['home_team_data']

        async def scraper(page):
            try:
                logger.debug("Scraping home team data...", extra={"tags": ["scraper", "home_team"]})
                url = await page.locator('.mc-summary__team.home a.mc-summary__badge-container').first.get_attribute('href')
                url = self._website_url + url

                match_result = await page.locator('.mc-summary__score').text_content()
                self.match_data['home_team_data']['score'] = int(match_result.split(' - ')[0])

                await self._request_handler.goto(page, url)
                self.match_data['home_team_data']['name'] = await page.locator('h2.club-header__team-name').text_content()

                logger.info("Home team data scraped", extra={"tags": ["scraper", "home_team"]})
                return self.match_data['home_team_data']
            except Exception as e:
                logger.error("Failed to scrape home team data", extra={"tags": ["scraper", "home_team"], "error": str(e)})
                raise

        return await self._create_context_then_callback(scraper)

    async def get_away_team_data(self) -> dict:
        self._raise_if_not_initialized()
        if self.match_data['away_team_data']['name'] and self.match_data['away_team_data']['score']:
            logger.debug("Returning cached away team data", extra={"tags": ["scraper", "away_team"]})
            return self.match_data['away_team_data']

        async def scraper(page):
            try:
                logger.debug("Scraping away team data...", extra={"tags": ["scraper", "away_team"]})
                url = await page.locator('.mc-summary__team.away a.mc-summary__badge-container').first.get_attribute('href')
                url = self._website_url + url

                match_result = await page.locator('.mc-summary__score').text_content()
                self.match_data['away_team_data']['score'] = int(match_result.split(' - ')[1])

                await self._request_handler.goto(page, url)
                self.match_data['away_team_data']['name'] = await page.locator('h2.club-header__team-name').text_content()

                logger.info("Away team data scraped", extra={"tags": ["scraper", "away_team"]})
                return self.match_data['away_team_data']
            except Exception as e:
                logger.error("Failed to scrape away team data", extra={"tags": ["scraper", "away_team"], "error": str(e)})
                raise

        return await self._create_context_then_callback(scraper)

    def _raise_if_not_initialized(self):
        if not self._initialized:
            logger.critical("Scraper method called before initialization", extra={"tags": ["scraper", "error"], "error": "UninitializedScraper"})
            raise RuntimeError("Scraper isn't initialized. Call 'await scraper.initialize()' first.")

    async def _create_context_then_callback(self, callback):
        try:
            async with async_playwright() as p:
                async with await p.chromium.launch(headless=True) as browser:
                    logger.debug("Browser launched", extra={"tags": ["scraper", "browser"]})
                    page = await browser.new_page()
                    page.set_default_timeout(0)  # FIXME: no timeout
                    await self._request_handler.goto(page, self._base_url)
                    logger.debug("Page navigation successful", extra={"tags": ["scraper", "browser"]})
                    return await callback(page)
        except Exception as e:
            logger.error("Error during Playwright context execution", extra={"tags": ["scraper", "browser"], "error": str(e)})
            raise
