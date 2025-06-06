from abc import ABC, abstractmethod
import os, sys, asyncio, inspect, subprocess
from sqlite3 import IntegrityError
from model.model_factory import ModelFactory

class ICommand(ABC):
    base_name: str
    description: str

    @abstractmethod
    def execute_command(self): pass

class ExitCommand(ICommand):
    base_name = 'exit'
    description = 'exit the program'

    def execute_command(self):
        print("Exiting...")
        sys.exit(0)

class HelpCommand(ICommand):
    base_name = 'help'
    description = 'get a list of commands with their description'

    def execute_command(self):
        commands = self._get_command_classes()

        print('available commands:')
        for command_cls in commands:
            
            print(f'\t{command_cls.base_name}: {command_cls.description}')

    def _get_command_classes(self) -> list[type]:
        current_module = sys.modules[__name__]
        return [obj for name, obj in inspect.getmembers(current_module, inspect.isclass)
            if obj.__module__ == __name__ and issubclass(obj, ICommand) and obj is not ICommand]

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
        
        async def coro():
            club_urls_scraper = ClubUrlsScraper()
            await club_urls_scraper.initialize()

            club_page_urls = await club_urls_scraper
            club_page_urls = club_page_urls[1:]

            async def scrape_club_data_and_save_to_database(club_url):
                club_scraper = ClubDataScraper()
                await club_scraper.initialize()

                club_data = club_scraper.get_all_data()

                try:
                    database_model.creat_record(club_data)
                except IntegrityError:
                    database_model.update_record(club_data)

            task_maker = lambda coroutine: asyncio.wait_for(asyncio.shield(coroutine), timeout=2)
            tasks = (task_maker(scrape_club_data_and_save_to_database(club_url)) for club_url in club_page_urls)
            await asyncio.gather(*tasks)

        asyncio.run(coro())

    def update_matches_model(self):
        from model.scrapers.match_data_scraper import MatchDataScraper
        from model.scrapers.match_urls_scraper import MatchUrlsScraper

        database_model = ModelFactory.create_model('matches')
        
        async def coro():
            match_urls_scraper = MatchUrlsScraper()
            await match_urls_scraper.initialize()

            match_page_urls = await match_urls_scraper.get_match_urls()

            async def scrape_match_data_and_save_to_database(match_url):
                match_scraper = MatchDataScraper()
                await match_scraper.initialize()

                match_data = await match_scraper.get_all_data()

                try:
                    database_model.creat_record(match_data)
                except IntegrityError:
                    database_model.update_record(match_data)

            await asyncio.gather(scrape_match_data_and_save_to_database(match_url) for match_url in match_page_urls)

        asyncio.run(coro())

    def update_players_model(self):
        from model.scrapers.player_data_scraper import PlayerDataScraper
        from model.scrapers.player_urls_scraper import PlayerUrlsScraper
        from model.scrapers.club_urls_scraper import ClubUrlsScraper

        database_model = ModelFactory.create_model('players')

        async def coro():
            club_urls_scraper = ClubUrlsScraper()
            await club_urls_scraper.initialize()

            club_page_urls = await club_urls_scraper.get_club_urls()
            club_page_urls = club_page_urls[1:]

            async def scrape_club_player_datas_and_update_database(club_page_url):
                player_urls_scraper = PlayerUrlsScraper(club_page_url)
                await player_urls_scraper.initialize()

                club_player_urls = await player_urls_scraper.get_club_player_urls()
                club_player_urls = club_player_urls[1:]

                async def scrape_player_data_and_update_database(player_page_url):
                    player_data_scraper = PlayerDataScraper(player_page_url)
                    await player_data_scraper.initialize()

                    player_data = player_data_scraper.get_all_data()

                    try:
                        database_model.creat_record(player_data)
                    except IntegrityError:
                        database_model.update_record(player_data)

                await asyncio.gather(scrape_player_data_and_update_database(player_page_url) for player_page_url in club_player_urls)
            
            await asyncio.gather(scrape_club_player_datas_and_update_database(club_url) for club_url in club_page_urls)

        asyncio.run(coro())


    def update_tables_model(self):
        from model.scrapers.tables_data_scraper import TablesDataScraper

        database_model = ModelFactory.create_model('tables')
        
        async def coro():
            tables_data_scraper = TablesDataScraper()   
            await tables_data_scraper.initialize()

            tables_data = await tables_data_scraper.get_tables_data()

            for standing in tables_data:
                try:
                    database_model.create_record(standing)
                except:
                    database_model.update_record(standing)

        asyncio.run(coro())

class ScrapeDataCommand(ICommand):
    base_name = 'scrape'
    description = 'scrape data with scraper and display in terminal'

    def __init__(self, *args):
        self.SCRAPE_REGISTERY = {
        "club_urls": ScrapeDataCommand.ClubUrlsScraper, 
        "club_data": ScrapeDataCommand.ClubDataScraper,
        "match_urls": ScrapeDataCommand.MatchUrlsScraper,
        "match_data": ScrapeDataCommand.MatchDataScraper,
        "player_urls": ScrapeDataCommand.PlayerUrlsScraper,
        "player_data": ScrapeDataCommand.PlayerDataScraper,
        "tables_data": ScrapeDataCommand.TablesDataScraper
    }
        self._type = args[0]
        self._arguments = args[1:]

        self._scraper = self.SCRAPE_REGISTERY[self._type](*self._arguments)

        self._printer = ScrapeDataCommand.Printer

    def execute_command(self):
        data = self._scraper.scrape_data()

        self._printer.print_data(data)

        while True:
            print()
            print("1. Done")
            print("2. save the data")
            print()

            choice = input("=> ")

            if choice == "1":
                break
            elif choice == "2":
                destination = self._choose_destination()
                file_name = self.type + self.get_date_string_for_filename()
                ScrapeDataCommand.DataExporter.export_data(data, file_name, destination)
                break

    # Get current timestamp and format it
    def get_date_string_for_filename(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def _choose_destination(self) -> str:
        import tkinter as tk
        from tkinter import filedialog

        # Hide the root Tkinter window
        root = tk.Tk()
        root.withdraw()

        folder_selected = filedialog.askdirectory(title="Select Destination Folder")
        return folder_selected

    class IScraper(ABC):
        @abstractmethod
        def scrape_data(self) -> list[tuple]: pass

        @abstractmethod
        def _validate_arguments(self, *args): pass

        def format_data(self, data: list[dict]) -> list[tuple]:
            columns_row = tuple(data[0].keys())
            result = []
            result.append(columns_row)
            for record in data:
                result.append(tuple(record.values()))
            return result

    class ClubUrlsScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)

        def scrape_data(self):
            asyncio.run(self._main())

        def _validate_arguments(self, *args):
            pass

        async def _main(self):
            from model.scrapers.club_urls_scraper import ClubUrlsScraper

            scraper = ClubUrlsScraper()
            await scraper.initialize()

            result = await scraper.get_club_urls()

            return result

    class ClubDataScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)
            self.arguments = args

        def scrape_data(self):
            result = asyncio.run(self._main())
            return result

        def format_data(self, data: list[dict]) -> list[tuple]:
            columns_row = list(data[0].keys())
            columns_row.remove('logo')
            result = []
            result.append(tuple(columns_row))
            for record in data:
                record.pop('logo')
                result.append(tuple(record.values()))
            return result

        def _validate_arguments(self, *args):
            if not args:
                raise ValueError('no club urls provided!')
            
        async def _main(self):
            from model.scrapers.club_data_scraper import ClubDataScraper

            tasks = []

            for url in self.arguments:
                scraper = ClubDataScraper(url)
                await scraper.initialize()
                
                tasks.append(scraper.get_all_data())

            result = await asyncio.gather(*tasks)
            result = self.format_data(result)
            return result

    class MatchUrlsScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)

        def scrape_data(self):
            asyncio.run(self._main())

        async def _main(self):
            from model.scrapers.match_urls_scraper import MatchUrlsScraper

            scraper = MatchUrlsScraper()
            await scraper.initialize()
            result = await scraper.get_match_urls()
            result = self.format_data(result)

            return result
        
        def _validate_arguments(self, *args):
            pass

        def format_data(self, data):
            result = []
            columns_row = ("url", "round")
            result.append(columns_row)

            for round, match_urls in data.values():
                for match_url in match_urls:
                    result.append((match_url, round))

            return result
        

    class MatchDataScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)
            
            self.match_urls = args

        def scrape_data(self):
            asyncio.run(self._main())
            
        async def _main(self):
            from model.scrapers.match_data_scraper import MatchDataScraper

            tasks = []

            for match_url in self.match_urls:
                scraper = MatchDataScraper(match_url)
                await scraper.initialize()
                tasks.append(scraper.get_all_data())

            result = await asyncio.gather(*tasks)
            result = self.format_data(result)

            return result

        def _validate_arguments(self, *args):
            if not args:
                raise ValueError('no match urls provided!')

    class PlayerUrlsScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)

            self.type = args[0]
            self.arguments = args[1:]

        def scrape_data(self):
            asyncio.run(self._main())

        async def _main(self):
            from model.scrapers.player_urls_scraper import PlayerUrlsScraper

            tasks = []

            for argument in self.arguments:
                if self.type == 'name':
                    scraper = PlayerUrlsScraper(club_name=argument)
                elif self.type == 'url':
                    scraper = PlayerUrlsScraper(url=argument)
                await scraper.initialize()

                tasks.append(scraper.get_club_player_urls())

            result = await asyncio.gather(*tasks)

            return result

        def _validate_arguments(self, *args):
            type = args.get(0)
            
            if not type:
                raise ValueError('no input type provided!\ntypes supported: url, name')
            elif type not in('name', 'url'):
                raise ValueError('input type provided is not valid!')

            type = "club name" if type == 'name' else type

            if not args[1:]:
                raise ValueError(f'no {type} provided!')

        def format_data(self, data: list[dict]) -> list[tuple]:
            columns_row = list(data[0].keys())
            columns_row.remove('picture')
            result = []
            result.append(tuple(columns_row))
            for record in data:
                record.pop('picture')
                result.append(tuple(record.values()))
            return result

    class PlayerDataScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)

            self.urls = args

        def scrape_data(self):
            asyncio.run(self._main())

        async def _main(self):
            from model.scrapers.player_data_scraper import PlayerDataScraper

            tasks = []

            for player_page_url in self.urls:
                scraper = PlayerDataScraper(player_page_url)
                await scraper.initialize()

                tasks.append(scraper.get_all_data())

            result = await asyncio.gather(*tasks)
            result = self.format_data(result)
            return result

        
        def _validate_arguments(self, *args):
            if not args:
                raise ValueError('no player page url provided!')

    class TablesDataScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)

        def scrape_data(self):
            asyncio.run(self._main())
        
        async def _main(self):
            from model.scrapers.tables_data_scraper import TablesDataScraper

            scraper = TablesDataScraper()
            await scraper.initialize()
            result = await scraper.get_tables_data()
            result = self.format_data(result)
            return result 

        def _validate_arguments(self, *args):
            pass

    class Printer:
        @staticmethod
        def print_data(data):
            import pandas as pd

            pd.set_option('display.max_colwidth', None)  # Don't truncate or wrap column content
            pd.set_option('display.width', None)         # Let it use full terminal width
            pd.set_option('display.expand_frame_repr', False)  # Prevent wrapping to multiple lines

            columns = data[0]
            data = data[1:]

            data_frame = pd.DataFrame(data, columns=columns)

            print(25 * "=")
            print(data_frame)
            print(25 * "=")

    class DataExporter:
        # FIXME
        pass

class TestCommand(ICommand):
    base_name = "tests"
    description = "Interactively run and explore test modules and test cases from the tests/ directory."

    def execute_command(self):
        script_path = os.path.join(os.path.dirname(__file__), "tests_controller.py")
        if os.path.exists(script_path):
            subprocess.run(["python", script_path])
        else:
            print("❌ tests_controller.py not found.")

class TestRequestHandler(ICommand):
    base_name = 'test_request_handler'
    description = 'test request handler'

    def __init__(self, *args):
        if not args:
            raise ValueError('no url provided!')

        self.arguments = args

    def execute_command(self):
        asyncio.run(self._main())

    async def _main(self):
        from model.scrapers.request_handler import RequestHandler

        handler = RequestHandler()
        await handler.configure()

        # Multiple URLs
        tasks = [handler.get(url) for url in self.arguments]
        try:
            results = await asyncio.gather(*tasks)
            # import pyperclip
            # pyperclip.copy(results[0])
            for i, result in enumerate(results, 1):
                print(f"\n--- Result {i} ---\n{result[:500]}...\n")

        except Exception as e:
            print(f"Error occurred: {e}")