from abc import ABC, abstractmethod
import os, asyncio
from model.database_manager import DatabaseManager
from model.model_factory import ModelFactory
from sqlite3 import IntegrityError

class ICommand(ABC):
    base_name: str
    description: str

    @abstractmethod
    def __init__(self, *args):  pass

    @abstractmethod
    def execute_command(self): pass

class DatabaseUpdate(ICommand):
    base_name = "db_update"
    description = "update database with updated data that scraped from the web"
    models = [
        'teams',
        'matches',
        'players',
        'tables'
    ]

    def __init__(self, *args):
        self.arguemnts = args
        self.model = args[0]

        if self.model not in  self.models:
            raise ValueError("unexpected model name provided, valid model names: 'teams', 'matches', 'players', 'tables'")

    def execute_command(self):
        if self.model == 'teams':
            self.update_teams_model()
        elif self.model == 'matches':
            self.update_matches_model
        elif self.model == 'players':
            self.update_players_model
        elif self.model == 'tables':
            self.update_tables_model()
        else:
            raise RuntimeError()

    def update_teams_model(self):
        from model.scrapers.club_data_scraper import ClubDataScraper
        from model.scrapers.club_urls_scraper import ClubUrlsScraper
        
        database_model = ModelFactory.create_model('teams')
        
        club_urls_scraper = ClubUrlsScraper()
        asyncio.run(club_urls_scraper.initialize())

        club_page_urls = asyncio.run(club_urls_scraper)

        async def scrape_club_data_and_save_to_database(club_url):
            club_scraper = ClubDataScraper()
            await club_scraper.initialize()

            club_data = club_scraper.get_all_data()

            try:
                database_model.creat_record(club_data)
            except IntegrityError:
                database_model.update_record(club_data)

        asyncio.gather(scrape_club_data_and_save_to_database(club_url) for club_url in club_page_urls)

    def update_matches_model(self):
        from model.scrapers.match_data_scraper import MatchDataScraper
        from model.scrapers.match_urls_scraper import MatchUrlsScraper

        database_model = ModelFactory.create_model('matches')
        
        match_urls_scraper = MatchUrlsScraper()
        asyncio.run(match_urls_scraper.initialize())

        match_page_urls = asyncio.run(match_urls_scraper.get_match_urls())

        async def scrape_match_data_and_save_to_database(match_url):
            match_scraper = MatchDataScraper()
            await match_scraper.initialize()

            match_data = match_scraper.get_all_data()

            try:
                database_model.creat_record(match_data)
            except IntegrityError:
                database_model.update_record(match_data)

        asyncio.gather(scrape_match_data_and_save_to_database(match_url) for match_url in match_page_urls)

    def update_players_model(self):
        from model.scrapers.player_data_scraper import PlayerDataScraper
        from model.scrapers.player_urls_scraper import PlayerUrlsScraper
        from model.scrapers.club_urls_scraper import ClubUrlsScraper

        club_urls_scraper = ClubUrlsScraper
        asyncio.run(club_urls_scraper.initialize())

        club_page_urls = club_urls_scraper.get_club_urls()

        database_model = ModelFactory.create_model('players')
        
        async def scrape_club_player_datas_and_update_database(club_page_url):
            player_urls_scraper = PlayerUrlsScraper(club_page_url)
            await player_urls_scraper.initialize()

            club_player_urls = await player_urls_scraper.get_club_player_urls()

            async def scrape_player_data_and_update_database(player_page_url):
                player_data_scraper = PlayerDataScraper(player_page_url)
                await player_data_scraper.initialize()

                player_data = player_data_scraper.get_all_data()

                try:
                    database_model.creat_record(player_data)
                except IntegrityError:
                    database_model.update_record(player_data)

            asyncio.gather(scrape_player_data_and_update_database(player_page_url) for player_page_url in club_player_urls)
        
        asyncio.gather(scrape_club_player_datas_and_update_database(club_url) for club_url in club_page_urls)


    def update_tables_model(self):
        from model.scrapers.tables_data_scraper import TablesDataScraper

        database_model = ModelFactory.create_model('tables')
        
        tables_data_scraper = TablesDataScraper()   
        asyncio.run(tables_data_scraper.initialize())

        tables_data = tables_data_scraper.get_tables_data()

        for standing in tables_data:
            try:
                database_model.create_record(standing)
            except:
                database_model.update_record(standing)