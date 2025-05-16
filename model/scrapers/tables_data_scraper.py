from model.scrapers.request_handler import RequestHandler
from model.scrapers.interfaces.tables_data_scraper import ITablesDataScraper
from model.scrapers.premierleague_website_scraper import PremierleagueWebsiteScraper
from bs4 import BeautifulSoup

class TablesDataScraper(PremierleagueWebsiteScraper, ITablesDataScraper):
    def __init__(self, url=None):
        super().__init__()
        if not url:
            url = "https://www.premierleague.com/tables"
    
        self._base_url = url

        self._initialized = False
        
        
    async def initialize(self):
        self._request_handler = RequestHandler()
        await self._request_handler.configure()

        structure = await self._request_handler.get(self._base_url)
        self._structure = BeautifulSoup(structure, 'html.parser')

        self._initialized = True
    
    async def get_tables_data(self):
        if not self._initialized:
            raise RuntimeError("the scraper doesn't initialized yet, run 'scraper.initialize() first'")

        table_rows = self._structure.select('tbody.league-table__tbody.isPL tr:not(.league-table__expandable.expandable)')
        print(len(table_rows))
        standings = []
        for table_row in table_rows:
            standings.append(await self._extract_data_from_tr_tag(table_row))

        return standings
    
    async def _extract_data_from_tr_tag(self, table_row):
        result = dict()

        position_string = table_row.select_one('td.league-table__pos.pos .league-table__value.value').get_text(strip=True)
        result['position'] = int(position_string)

        result['team_name'] = table_row.select_one('td.league-table__team.team .league-table__team-name--long').get_text(strip=True).lower()

        played_value_string = table_row.select_one('td:nth-child(3)').get_text(strip=True)
        result['played'] = int(played_value_string)

        won_value_string = table_row.select_one('td:nth-child(4)').get_text(strip=True)
        result['won'] = int(won_value_string)

        drawn_value_string = table_row.select_one('td:nth-child(5)').get_text(strip=True)
        result['drawn'] = int(drawn_value_string)

        lost_value_string = table_row.select_one('td:nth-child(6)').get_text(strip=True)
        result['lost'] = int(lost_value_string)

        goals_for_value_string = table_row.select_one('td:nth-child(7)').get_text(strip=True)
        result['goals_for'] = int(goals_for_value_string)

        goals_against_value_string = table_row.select_one('td:nth-child(8)').get_text(strip=True)
        result['goals_against'] = int(goals_against_value_string)

        goals_difference_value_string = table_row.select_one('td:nth-child(9)').get_text(strip=True)
        result['goals_difference'] = int(goals_difference_value_string)

        points_value_string = table_row.select_one('td.league-table__points.points').get_text(strip=True)
        result['points'] = int(points_value_string)

        return result