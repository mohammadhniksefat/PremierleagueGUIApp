from bs4 import BeautifulSoup
import re
from .utils import UrlValidator
from .request_handler import RequestHandler
from .interfaces.club_data_scraper import IClubDataScraper
from .premierleague_website_scraper import PremierleagueWebsiteScraper

class ClubDataScraper(PremierleagueWebsiteScraper, IClubDataScraper):
    def __init__(self, url):
        if not UrlValidator.validate_club_page_url(url):
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

    async def initialize(self):
        main_page_url = self._base_url
        directory_page_url = self._base_url.replace('overview', 'directory')

        self._request_handler = RequestHandler()
        await self._request_handler.configure()

        main_page_structure = await self._request_handler.get(main_page_url)
        directory_page_structure = await self._request_handler.get(directory_page_url)

        self._structures = dict()

        self._structures['main_page'] = BeautifulSoup(main_page_structure, 'html.parser') 
        self._structures['directory_page'] = BeautifulSoup(directory_page_structure, 'html.parser')

        self._initialized = True

    async def get_all_data(self) -> dict:
        self._raise_if_not_initialized()

        self.club_data['club_name'] = await self.get_club_name()
        self.club_data['establishment_year'] = await self.get_establishment_year()
        self.club_data['manager_name'] = await self.get_manager_name()
        self.club_data['city'] = await self.get_city_name()
        self.club_data['stadium'] = await self.get_stadium_name()
        self.club_data['logo'] = await self.get_club_logo()
        self.club_data['squad_page_url'] = await self.get_squad_page_url()

        return self.club_data

    async def get_club_name(self):
        self._raise_if_not_initialized()
        
        if self.club_data['club_name']:
            return self.club_data['club_name']

        self.club_data['club_name'] = self._structures['main_page'].select_one('h2.club-header__team-name').get_text(strip=True)
        return self.club_data['club_name']

    async def get_establishment_year(self):
        self._raise_if_not_initialized()

        if self.club_data['establishment_year']:
            return self.club_data['establishment_year']

        establishment_year = self._structures['main_page'].select_one('.club-header__club-info span')
        self.club_data['establishment_year'] = re.search(r'\d+', establishment_year.get_text(strip=True)).group()
        return self.club_data['establishment_year']
    
    async def get_manager_name(self):
        self._raise_if_not_initialized()

        if self.club_data['manager_name']:
            return self.club_data['manager_name']

        selectors = [
            r'^Head Coach$', 
            r'^First-team Manager$',
            r'^Manager$'
            ]
        pattern = re.compile(r'|'.join(selectors), re.IGNORECASE)

        title_element = self._structures['directory_page'].find(string=pattern)
        self.club_data['manager_name'] = title_element.parent.parent.parent.parent.select_one('.cardBody').get_text(strip=True)

        return self.club_data['manager_name']

    async def get_city_name(self):
        self._raise_if_not_initialized()

        if self.club_data['city']:
            return self.club_data['city']

        city = self._structures['main_page'].select_one('span.club-header__club-stadium')
        self.club_data['city'] = city.text.split(',')[1].strip()
        return self.club_data['city']

    async def get_stadium_name(self):
        self._raise_if_not_initialized()

        if self.club_data['stadium']:
            return self.club_data['stadium']

        stadium = self._structures['main_page'].select_one('span.club-header__club-stadium')
        self.club_data['stadium'] = stadium.text.split(',')[0].strip()
        return self.club_data['stadium']
    
    async def get_club_logo(self):
        self._raise_if_not_initialized()

        if self.club_data['logo']:
            return self.club_data['logo']

        logo_url = self._structures['main_page'].select_one('.club-header__content img.club-header__badge')
        logo_url = logo_url['src']
        logo_data = await self._request_handler.get(logo_url, raw=True)
        self.club_data['logo'] = logo_data

        return self.club_data['logo']
    
    async def get_squad_page_url(self):
        self._raise_if_not_initialized()

        if self.club_data['squad_page_url']:
            return self.club_data['squad_page_url']

        squad_page_url = self._structures['main_page'].select_one('.tab.club-navigation__tab:nth-child(2) a')['href']
        self.club_data['squad_page_url'] = self._base_url.replace('overview', squad_page_url)
        return self.club_data['squad_page_url']
    
    def _raise_if_not_initialized(self):
        if not self._initialized:
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")