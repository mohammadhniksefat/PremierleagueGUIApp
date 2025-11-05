import logging
from bs4 import BeautifulSoup
from premierleague.model.scrapers.request_handler import RequestHandler
from premierleague.model.scrapers.interfaces.tables_data_scraper import ITablesDataScraper
from premierleague.model.scrapers.premierleague_website_scraper import PremierleagueWebsiteScraper
from premierleague.log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(RequestHandler))

class TablesDataScraper(PremierleagueWebsiteScraper, ITablesDataScraper):
    def __init__(self, url=None):
        super().__init__()
        if not url:
            url = "https://www.premierleague.com/tables"
            logger.debug("No URL provided, using default tables URL", extra={"tags": ["init"]})

        self._base_url = url
        self._initialized = False
        logger.debug(f"TablesDataScraper instance created with URL: {self._base_url}", extra={"tags": ["init"]})

    async def initialize(self):
        logger.info("Initializing TablesDataScraper...", extra={"tags": ["init"]})
        try:
            self._request_handler = RequestHandler()
            await self._request_handler.configure()
            logger.debug("RequestHandler configured", extra={"tags": ["request_handler"]})

            structure = await self._request_handler.get(self._base_url)
            self._structure = BeautifulSoup(structure, 'html.parser')
            self._initialized = True
            logger.info("TablesDataScraper initialized successfully", extra={"tags": ["init"]})
        except Exception as e:
            logger.exception("Failed to initialize TablesDataScraper", extra={"tags": ["init", "error"], "error": str(e)})
            raise

    async def get_tables_data(self):
        if not self._initialized:
            logger.critical("Attempted to get table data before initialization", extra={"tags": ["usage_error", "error"], "error": "Scraper not initialized"})
            raise RuntimeError("the scraper doesn't initialized yet, run 'scraper.initialize() first'")

        logger.info("Extracting table data from page structure", extra={"tags": ["scraping", "tables"]})
        try:
            table_rows = self._structure.select('tbody.league-table__tbody.isPL tr:not(.league-table__expandable.expandable)')
            logger.debug(f"Found {len(table_rows)} table rows in Premier League table", extra={"tags": ["scraping", "tables"]})

            standings = []
            for i, table_row in enumerate(table_rows):
                try:
                    team_data = await self._extract_data_from_tr_tag(table_row)
                    standings.append(team_data)
                    logger.debug(f"Extracted data for row #{i + 1}: {team_data}", extra={"tags": ["scraping", "team_row"]})
                except Exception as e:
                    logger.error(f"Error extracting data from row #{i + 1}", extra={"tags": ["scraping", "error"], "error": str(e)})
                    continue

            logger.info(f"Successfully extracted standings for {len(standings)} teams", extra={"tags": ["scraping", "tables"]})
            return standings
        except Exception as e:
            logger.exception("Failed to extract table data", extra={"tags": ["scraping", "error"], "error": str(e)})
            raise

    async def _extract_data_from_tr_tag(self, table_row):
        result = {}
        try:
            result['position'] = int(table_row.select_one('td.league-table__pos.pos .league-table__value.value').get_text(strip=True))
            result['team_name'] = table_row.select_one('td.league-table__team.team .league-table__team-name--long').get_text(strip=True).lower()
            result['played'] = int(table_row.select_one('td:nth-child(3)').get_text(strip=True))
            result['won'] = int(table_row.select_one('td:nth-child(4)').get_text(strip=True))
            result['drawn'] = int(table_row.select_one('td:nth-child(5)').get_text(strip=True))
            result['lost'] = int(table_row.select_one('td:nth-child(6)').get_text(strip=True))
            result['goals_for'] = int(table_row.select_one('td:nth-child(7)').get_text(strip=True))
            result['goals_against'] = int(table_row.select_one('td:nth-child(8)').get_text(strip=True))
            result['goals_difference'] = int(table_row.select_one('td:nth-child(9)').get_text(strip=True))
            result['points'] = int(table_row.select_one('td.league-table__points.points').get_text(strip=True))
            return result
        except Exception as e:
            logger.exception("Error parsing table row", extra={"tags": ["row_parsing", "error"], "error": str(e)})
            raise
