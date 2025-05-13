from bs4 import BeautifulSoup
from .request_handler import RequestHandler
from .interfaces.club_urls_scraper import IClubUrlsScraper
from .interfaces.premierleague_website_scraper import PremierleagueWebsiteScraper

class ClubUrlsScraper(PremierleagueWebsiteScraper, IClubUrlsScraper):
    def __init__(self, url=None):
        super().__init__()
        self._base_url = url if url else self._website_url + '/clubs?se=578'
        
    async def initialize(self):

        self._request_handler = RequestHandler()
        await self._request_handler.configure()

        structure = await self._request_handler.get(self._base_url)
        self._structure = BeautifulSoup(structure, 'html.parser')

    async def get_club_urls(self):
        clubs = self._structure.select('.club-cards-wrapper .club-list .club-card-wrapper a')
        club_urls = list(map(lambda club: str(self._website_url + club.get('href')), clubs))
        club_names = list(map(lambda club: club.select_one('.club-card__info .club-card__name-container h2').get_text(strip=True), clubs))

        combined_dictionary = {club.select_one('.club-card__info .club-card__name-container h2').get_text(strip=True): \
                               str(self._website_url + club.get('href')) \
                               for club in clubs}
        
        return combined_dictionary