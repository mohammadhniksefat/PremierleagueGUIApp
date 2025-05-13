import re
from bs4 import BeautifulSoup
from .interfaces.player_data_scraper import IPlayerDataScraper
from .utils import UrlValidator
from .request_handler import RequestHandler
from .interfaces.premierleague_website_scraper import PremierleagueWebsiteScraper

class PlayerDataScraper(PremierleagueWebsiteScraper, IPlayerDataScraper):
    def __init__(self, url):
        if not UrlValidator.validate_player_page_url(url):
            raise ValueError("the url provided isn't valid")
        
        super().__init__()

        self._base_url = url
        self._initialized = False
        self.player_data = {
            'firstname': str(),
            'lastname': str(),
            'club_name':str(),
            'position': str(),
            'nationality': str(),
            'date_of_birth': str(),
            'shirt_number': str(),
            'age': int(),
            'height': int(),
            'picture': bytes()
        }
    
    async def initialize(self) -> None:
        self._request_handler = RequestHandler()
        await self._request_handler.configure()

        structure = await self._request_handler.get(self._base_url)

        self._structures = {
            'main': BeautifulSoup(structure, 'html.parser')
        }

        self._initialized = True

    async def get_all_data(self) -> dict:
        self._raise_if_not_initialized()

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

        return self.player_data

    async def get_club_name(self):
        self._raise_if_not_initialized()

        if self.player_data['club_name']:
            return self.player_data['club_name']
        
        club_name = self._structures['main'].select_one('.playerSidebar .player-overview__side-widget:first-child .player-overview__col .player-overview__info a')
        self.player_data['club_name'] = club_name.get_text(strip=True)
        return self.player_data['club_name']

    async def get_firstname(self):
        self._raise_if_not_initialized()

        if self.player_data['firstname']:
            return self.player_data['firstname']

        self.player_data['firstname'] = self._structures['main'].select_one('.player-header__name-first').get_text(strip=True)
        return self.player_data['firstname']

    async def get_lastname(self):
        self._raise_if_not_initialized()

        if self.player_data['lastname']:
            return self.player_data['lastname']

        self.player_data['lastname'] = self._structures['main'].select_one('.player-header__name-last').get_text(strip=True)
        return self.player_data['lastname']

    async def get_position(self):
        self._raise_if_not_initialized()

        if self.player_data['position']:
            return self.player_data['position']

        self.player_data['position'] = self._structures['main'].select_one('.playerSidebar .player-overview.u-hide-mob .player-overview__side-widget:first-child > .player-overview__col:nth-child(3) .player-overview__info').get_text(strip=True)
        return self.player_data['position']

    async def get_nationality(self):
        self._raise_if_not_initialized()

        if self.player_data['nationality']:
            return self.player_data['nationality']

        self.player_data['nationality'] = self._structures['main'].select_one('.player-info__player-country').get_text(strip=True)
        return self.player_data['nationality']

    async def get_shirt_number(self):
        self._raise_if_not_initialized()

        if self.player_data['shirt_number']:
            return self.player_data['shirt_number']

        self.player_data['shirt_number'] = self._structures['main'].select_one('.player-header div.player-header__player-number').get_text(strip=True)  
        return self.player_data['shirt_number']

    async def get_date_of_birth(self):
        self._raise_if_not_initialized()

        if self.player_data['date_of_birth']:
            return self.player_data['date_of_birth']

        items = self._structures['main'].select_one('.player-info__details-list .player-info__col:nth-child(2) .player-info__info')
        items = items.get_text(strip=True).split('  ')
        self.player_data['date_of_birth'] = items[0]
        return self.player_data['date_of_birth']

    async def get_age(self):
        self._raise_if_not_initialized()

        if self.player_data['age']:
            return self.player_data['age']

        items = self._structures['main'].select_one('.player-info__details-list .player-info__col:nth-child(2) .player-info__info')
        items = items.get_text(strip=True).split('  ')
        age_text = items[1]
        self.player_data['age'] = int(re.search(r'\d+', age_text).group())
        return self.player_data['age']
        
    async def get_height(self):
        self._raise_if_not_initialized()

        if self.player_data['height']:
            return self.player_data['height']

        height_string = self._structures['main'].select_one('.player-info__col:nth-child(3) .player-info__info').get_text(strip=True)
        self.player_data['height'] = int(re.match(r'\d+', height_string).group())
        return self.player_data['height'] 

    async def get_picture(self):
        self._raise_if_not_initialized()

        if self.player_data['picture']:
            return self.player_data['picture']

        picture_url = self._structures['main'].select_one('.imgContainer img.img')['src']
        print(picture_url)
        self.player_data['picture'] = await self._request_handler.get(url=picture_url, raw=True)
        return self.player_data['picture']
    
    def _raise_if_not_initialized(self):
        if not self._initialized:
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")