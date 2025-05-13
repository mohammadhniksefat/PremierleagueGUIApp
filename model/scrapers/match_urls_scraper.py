from .interfaces.match_urls_scraper import IMatchUrlsScraper
from .request_handler import PlaywrightRequestHandler
from .interfaces.premierleague_website_scraper import PremierleagueWebsiteScraper
from playwright.async_api import async_playwright
import asyncio, re

class MatchUrlsScraper(PremierleagueWebsiteScraper, IMatchUrlsScraper):
    def __init__(self, url=None):
        PremierleagueWebsiteScraper.__init__(self)
        self._base_url = url if url else self._website_url + '/matchweek/18390/blog?match=true'
        self._initialized = False

    async def initialize(self) -> None:
        self._request_handler = PlaywrightRequestHandler()
        await self._request_handler.configure()
        self._initialized = True

    async def _get_week_match_urls(self, browser, url):
        page = await browser.new_page()
        page.set_default_timeout(0)
        await self._request_handler.goto(page, url)

        result = dict()

        round = re.search(r'\d+', await page.locator('.fixtures-abridged-header__title').first.text_content()).group()
        result['round'] = int(round)
        result['urls'] = set()

        game_elements = page.locator('a.match-fixture--abridged.match-fixture')
        for i in range(await game_elements.count()):
            match_url = await game_elements.nth(i).get_attribute('href')
            match_url = self._website_url + match_url
            result['urls'].add(match_url)

        print(len(result['urls']))
        print(result['urls'])
        return result

    async def _get_week_page_urls(self, browser):
        page = await browser.new_page()
        page.set_default_timeout(0)
        await self._request_handler.goto(page, self._base_url)
        await page.evaluate('''
        const element = document.querySelector('header.mc-header')
        element.classList.add('is-open')
''')
        week_urls = page.locator('.mc-header__gameweek-selector-list-container .mc-header__gameweek-selector-list li.mc-header__gameweek-selector-list-item a')
        result = []
        for i in range(await week_urls.count()):
            week_anchortag = week_urls.nth(i)
            url = self._website_url + await week_anchortag.get_attribute('href')
            result.append(url)
        result = result[:int(len(result) / 2)]
        return result

    async def get_match_urls(self) -> dict[int, list[str]]:
        self._raise_if_not_initialized()

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            week_page_urls = await self._get_week_page_urls(browser)
            tasks = [self._get_week_match_urls(browser, url) for url in week_page_urls]
            match_urls = await asyncio.gather(*tasks)
            
            result: dict[str, list] = dict()
            for match_url_dict in match_urls:
                result[match_url_dict['round']] = match_url_dict['urls']

            await browser.close()

            return result
        
    def _raise_if_not_initialized(self):
        if not self._initialized:
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")   
