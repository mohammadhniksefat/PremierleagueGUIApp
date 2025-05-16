from .interfaces.match_data_scraper import IMatchDataScraper
from .utils import UrlValidator
from .request_handler import PlaywrightRequestHandler
from .premierleague_website_scraper import PremierleagueWebsiteScraper
from playwright.async_api import async_playwright
import re

class MatchDataScraper(PremierleagueWebsiteScraper, IMatchDataScraper):
    def __init__(self, url):
        if not UrlValidator.validate_match_page_url(url):
            raise ValueError("the url provided isn't valid")
        
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
            'away_team_data':{
                'name': str(),
                'score': int()
            }
        }

    async def initialize(self) -> None:
        self._request_handler = PlaywrightRequestHandler()
        await self._request_handler.configure()
        self._initialized = True

    async def get_all_data(self) -> dict:
        self._raise_if_not_initialized()

        async def scraper(page):
            round_number = await page.locator('.mc-header__gameweek-selector-current-gameweek--long').first.text_content()
            self.match_data['round_number'] = int(re.search(r'\d+', round_number).group())

            self.match_data['timestamp'] = int(await page.locator('.mc-summary__info-kickoff .renderKOContainer').first.get_attribute('data-kickoff'))
            
            self.match_data['referee_name'] = await page.locator('.mc-summary__info:last-child').text_content().lstrip('Ref: ')

            home_team_page_url = await page.locator('.mc-summary__team-container:nth-child(1) a.mc-summary__badge-container').first.get_attribute('href') 

            away_team_page_url = await page.locator('.mc-summary__team-container:nth-child(2) a.mc-summary__badge-container').first.get_attribute('href')

            match_result = await page.locator('.mc-summary__score').text_content().spilt(' - ') 

            self.match_data['home_team_data']['score'] = match_result[0]
            self.match_data['away_team_data']['score'] = match_result[1]

            await self._request_handler.goto(page, home_team_page_url)
            self.match_data['home_team_data']['team_name'] = await page.locator('h2.club-header__team-name').text_content()

            await self._request_handler.goto(page, away_team_page_url)
            self.match_data['away_team_data']['team_name'] = await page.locator('h2.club-header__team-name').text_content()

            return self.match_data

        return await self._create_context_then_callback(scraper)

    async def get_timestamp(self) -> int:
        self._raise_if_not_initialized()
    
        if self.match_data['timestamp']:
            return self.match_data['timestamp']
        
        async def scraper(page):
            print('scraping started!')
            self.match_data['timestamp'] = int(await page.locator('.mc-summary__info-kickoff .renderKOContainer').first.get_attribute('data-kickoff'))
            return self.match_data['timestamp']

        return await self._create_context_then_callback(scraper)    

    async def get_round_number(self) -> int:
        self._raise_if_not_initialized()
    
        if self.match_data['round_number']:
            return self.match_data['round_number']

        async def scraper(page):
            print('scraping started!')
            element = page.locator('.mc-header__gameweek-selector-current-gameweek--long').first
            print(f'element found {element}')
            string = await element.text_content()
            self.match_data['round_number'] = int(re.search(r'\d+', string).group())
            return self.match_data['round_number']
        
        return await self._create_context_then_callback(scraper)
    
    async def get_referee_name(self) -> str:
        self._raise_if_not_initialized()

        if self.match_data['referee_name']:
            return self.match_data['referee_name']
        
        async def scraper(page):
            referee_name = await page.locator('.mc-summary__info:last-child').text_content()
            print(referee_name)
            self.match_data['referee_name'] = referee_name.strip().lstrip('Ref: ')
            return self.match_data['referee_name']
        
        return await self._create_context_then_callback(scraper)
    
    async def get_home_team_data(self) -> dict:
        self._raise_if_not_initialized()

        if self.match_data['home_team_data']['name'] and self.match_data['home_team_data']['score']:
            return self.match_data['home_team_data']
    
        async def scraper(page):
            home_team_page_url = await page.locator('.mc-summary__team.home a.mc-summary__badge-container').first.get_attribute('href')
            home_team_page_url = self._website_url + home_team_page_url

            match_result = await page.locator('.mc-summary__score').text_content()
            match_result = match_result.split(' - ') 
            self.match_data['home_team_data']['score'] = int(match_result[0])

            await self._request_handler.goto(page, home_team_page_url)
            self.match_data['home_team_data']['name'] = await page.locator('h2.club-header__team-name').text_content()

            return self.match_data['home_team_data']

        return await self._create_context_then_callback(scraper)

    async def get_away_team_data(self) -> dict:
        self._raise_if_not_initialized()

        if self.match_data['away_team_data']['name'] and self.match_data['away_team_data']['score']:
            return self.match_data['away_team_data']
    
        async def scraper(page):
            home_team_page_url = await page.locator('.mc-summary__team.away a.mc-summary__badge-container').first.get_attribute('href')
            home_team_page_url = self._website_url + home_team_page_url 

            match_result = await page.locator('.mc-summary__score').text_content()
            match_result = match_result.split(' - ') 
            self.match_data['away_team_data']['score'] = int(match_result[1])

            await self._request_handler.goto(page, home_team_page_url)
            self.match_data['away_team_data']['name'] = await page.locator('h2.club-header__team-name').text_content()

            return self.match_data['away_team_data']

        return await self._create_context_then_callback(scraper)


    def _raise_if_not_initialized(self):
        if not self._initialized:
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")
        
    async def _create_context_then_callback(self, callback):
        async with async_playwright() as p:
            async with await p.chromium.launch(headless=True) as browser:
                page = await browser.new_page()
                page.set_default_timeout(0)
                await self._request_handler.goto(page, self._base_url)
                return await callback(page)

