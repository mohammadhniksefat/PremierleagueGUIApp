import logging
import asyncio, re
from playwright.async_api import async_playwright
from .interfaces.match_urls_scraper import IMatchUrlsScraper
from premierleague.model.scrapers.request_handler import PlaywrightRequestHandler
from premierleague.model.scrapers.premierleague_website_scraper import PremierleagueWebsiteScraper
from premierleague.log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(PlaywrightRequestHandler))

class MatchUrlsScraper(PremierleagueWebsiteScraper, IMatchUrlsScraper):
    def __init__(self, url=None):
        PremierleagueWebsiteScraper.__init__(self)
        self._base_url = url if url else self._website_url + '/matchweek/18390/blog?match=true'
        self._initialized = False
        logger.debug("MatchUrlsScraper instantiated", extra={"tags": ["init"], "base_url": self._base_url})

    async def initialize(self) -> None:
        logger.info("Initializing MatchUrlsScraper", extra={"tags": ["init"]})
        try:
            self._request_handler = PlaywrightRequestHandler()
            await self._request_handler.configure()
            self._initialized = True
            logger.info("MatchUrlsScraper successfully initialized", extra={"tags": ["init"]})
        except Exception as e:
            logger.exception("Initialization failed", extra={"tags": ["init", "error"], "error": str(e)})
            raise

    async def _get_week_match_urls(self, browser, url):
        logger.debug(f"Fetching match URLs from week page: {url}", extra={"tags": ["scraping", "week_page"]})
        try:
            page = await browser.new_page()
            page.set_default_timeout(0)
            await self._request_handler.goto(page, url)

            result = dict()

            round_text = await page.locator('.fixtures-abridged-header__title').first.text_content()
            round_number = re.search(r'\d+', round_text).group()
            result['round'] = int(round_number)
            result['urls'] = set()

            logger.debug(f"Scraping match URLs for round {result['round']}", extra={"tags": ["scraping", "match_urls"]})

            game_elements = page.locator('a.match-fixture--abridged.match-fixture')
            count = await game_elements.count()
            logger.debug(f"Found {count} match elements", extra={"tags": ["scraping", "match_urls"]})

            for i in range(count):
                match_url = await game_elements.nth(i).get_attribute('href')
                full_url = self._website_url + match_url
                result['urls'].add(full_url)

            logger.info(f"Scraped {len(result['urls'])} match URLs for round {result['round']}", extra={"tags": ["scraping", "match_urls"]})
            return result
        except Exception as e:
            logger.exception("Failed to scrape week match URLs", extra={"tags": ["scraping", "error"], "error": str(e), "url": url})
            raise

    async def _get_week_page_urls(self, browser):
        logger.debug("Fetching all week page URLs", extra={"tags": ["scraping", "week_pages"]})
        try:
            page = await browser.new_page()
            page.set_default_timeout(0)
            await self._request_handler.goto(page, self._base_url)

            await page.evaluate('''
                const element = document.querySelector('header.mc-header');
                element.classList.add('is-open');
            ''')

            week_urls = page.locator(
                '.mc-header__gameweek-selector-list-container .mc-header__gameweek-selector-list li.mc-header__gameweek-selector-list-item a'
            )

            result = []
            count = await week_urls.count()
            logger.debug(f"Found {count} week links", extra={"tags": ["scraping", "week_pages"]})

            for i in range(count):
                week_anchor = week_urls.nth(i)
                href = await week_anchor.get_attribute('href')
                full_url = self._website_url + href
                result.append(full_url)

            half_result = result[:int(len(result) / 2)]
            logger.info(f"Extracted {len(half_result)} week page URLs", extra={"tags": ["scraping", "week_pages"]})
            return half_result
        except Exception as e:
            logger.exception("Failed to get week page URLs", extra={"tags": ["scraping", "error"], "error": str(e)})
            raise

    async def get_match_urls(self) -> dict[int, list[str]]:
        self._raise_if_not_initialized()
        logger.info("Starting full match URL scraping", extra={"tags": ["scraping", "full_process"]})

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                logger.debug("Launched Chromium browser", extra={"tags": ["browser", "launch"]})

                week_page_urls = await self._get_week_page_urls(browser)
                logger.debug(f"Week URLs to process: {len(week_page_urls)}", extra={"tags": ["scraping", "week_pages"]})

                tasks = [self._get_week_match_urls(browser, url) for url in week_page_urls]
                match_urls = await asyncio.gather(*tasks)

                result: dict[int, list] = dict()
                for match_url_dict in match_urls:
                    round_number = match_url_dict['round']
                    urls = list(match_url_dict['urls'])
                    result[round_number] = urls
                    logger.debug(f"Round {round_number}: {len(urls)} match URLs collected", extra={"tags": ["scraping", "match_urls"]})

                await browser.close()
                logger.info("Successfully completed match URL scraping", extra={"tags": ["scraping", "full_process"]})
                return result
        except Exception as e:
            logger.exception("Failed during match URL scraping", extra={"tags": ["scraping", "error"], "error": str(e)})
            raise

    def _raise_if_not_initialized(self):
        if not self._initialized:
            logger.critical("Scraper used before initialization", extra={"tags": ["usage_error", "error"], "error": "Scraper not initialized"})
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")
