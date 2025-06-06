from bs4 import BeautifulSoup
from .interfaces.player_urls_scraper import IPlayerUrlsScraper
from .utils import UrlValidator
from .request_handler import RequestHandler
from .club_urls_scraper import ClubUrlsScraper
from .premierleague_website_scraper import PremierleagueWebsiteScraper

class PlayerUrlsScraper(PremierleagueWebsiteScraper, IPlayerUrlsScraper):
    def __init__(self, club_name=None, url=None):
        super().__init__()
        self._club_name = club_name
        self._url = url
        self._initialized = False

    async def initialize(self) -> None:
        self._request_handler = RequestHandler()
        await self._request_handler.configure()

        if self._url:
            if not UrlValidator.validate_squad_page_url(self._url):
                # if it was club page instead of squad page it should find the squad page url
                self._url = await self._scrap_squad_page_url(club_page_url=self._url)
        elif self._club_name:
            self._url = await self._scrap_squad_page_url(club_name=self._club_name)
        else:
            raise ValueError("didn't provided any identifier")
        
        self.structure = await self._request_handler.get(self._url)
        self.structure = BeautifulSoup(self.structure, 'html.parser')

        self._initialized = True

    async def get_club_player_urls(self) -> dict[str, str]:
        self._raise_if_not_initialized()
        
        result = []

        columns_row = ("player_name", "player_page_url")
        result.append(columns_row)

        player_elements = self.structure.select('li.stats-card[data-widget="featured-player"] a.stats-card__wrapper')
        for player_element in player_elements:
            firstname = player_element.select_one('.stats-card__player-first').get_text(strip=True)
            lastname = player_element.select_one('.stats-card__player-last').get_text(strip=True)
            full_name = firstname + lastname

            player_page_url = self._website_url + player_element.get('href')

            result.append((full_name, player_page_url))

        return result

    async def _scrap_squad_page_url(self, club_name=None, club_page_url=None):
        if club_page_url:
            pass
        elif club_name:
            scraper = ClubUrlsScraper()
            await scraper.initialize()

            club_page_url = scraper.get_club_urls()[club_name]
            squad_page_url = await self._scrap_squad_page_url(club_page_url=club_page_url)
        else:
            raise ValueError("didn't provided any argument")
        
        page_structure = await self._request_handler.get(club_page_url)
        page_structure = BeautifulSoup(page_structure, 'html.parser')
        squad_button = page_structure.select_one('ul.club-navigation__nav a.club-navigation__link[data-text="Squad"]')
        squad_page_url = squad_button.get('href')
        return club_page_url.replace('overview', squad_page_url)
    
    def _raise_if_not_initialized(self):
        if not self._initialized:
            raise RuntimeError("scraper doesn't initialized yet, you should call 'await scraper.initialize()' first")


