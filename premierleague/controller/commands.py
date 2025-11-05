from abc import ABC, abstractmethod
import os, sys, asyncio, inspect, subprocess, time
from sqlite3 import IntegrityError
from model.model_factory import ModelFactory
from log_config.logger_configurer import configure_logger, resolve_class_module_name
import logging, traceback

logger = logging.getLogger(__name__)
configure_logger(resolve_class_module_name(ModelFactory))

class ICommand(ABC):
    base_name: str
    description: str

    @abstractmethod
    def execute_command(self):
        pass

class ExitCommand(ICommand):
    base_name = 'exit'
    description = 'exit the program'

    def execute_command(self):
        logger.info("Program exiting initiated", extra={"tags": ["event"], "event_type": "shutdown"})
        print("Exiting...")
        sys.exit(0)

class HelpCommand(ICommand):
    base_name = 'help'
    description = 'get a list of commands with their description'

    def execute_command(self):
        commands = self._get_command_classes()
        logger.info("Help command executed", extra={"tags": ["event"], "event_type": "help_requested"})
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
        if self.model not in self.models:
            logger.error("Invalid model name provided", extra={
                "tags": ["validation", "exception"],
                "field": "model", "value": self.model, "result": "failed",
                "error": f"ValueError: unexpected model name {self.model}"
            })
            raise ValueError("unexpected model name provided, valid model names: 'teams', 'matches', 'players', 'tables'")
        logger.info("DatabaseUpdate command initialized", extra={"tags": ["event"], "event_type": "command_init", "resource": self.model})

    def execute_command(self):
        logger.info("Database update started", extra={"tags": ["event"], "event_type": "db_update", "resource": self.model})
        if self.model == 'teams':
            self.update_teams_model()
        elif self.model == 'matches':
            self.update_matches_model()
        elif self.model == 'players':
            self.update_players_model()
        elif self.model == 'tables':
            self.update_tables_model()
        else:
            logger.critical("Unexpected runtime condition reached in execute_command", extra={"tags": ["exception"], "error": "RuntimeError"})
            raise RuntimeError()

    def update_teams_model(self):
        from model.scrapers.club_data_scraper import ClubDataScraper
        from model.scrapers.club_urls_scraper import ClubUrlsScraper

        configure_logger(resolve_class_module_name(ClubDataScraper))
        configure_logger(resolve_class_module_name(ClubUrlsScraper))

        database_model = ModelFactory.create_model('teams')

        async def coro():
            try:
                club_urls_scraper = ClubUrlsScraper()
                await club_urls_scraper.initialize()
                club_page_urls = await club_urls_scraper.get_club_urls()
                logger.debug("Club URLs fetched", extra={"tags": ["network"], "destination": "club_urls_source", "method": "GET"})
                club_page_urls = club_page_urls[1:]

                async def scrape_club_data_and_save_to_database(club_url):
                    club_scraper = ClubDataScraper()
                    await club_scraper.initialize()
                    club_data = club_scraper.get_all_data()

                    try:
                        database_model.creat_record(club_data)
                        logger.info("Club data inserted", extra={"tags": ["event", "access"], "resource": "teams"})
                    except IntegrityError as e:
                        database_model.update_record(club_data)
                        logger.warning("Duplicate club data updated", extra={"tags": ["warning"], "error": str(e), "resource": "teams"})

                tasks = [asyncio.wait_for(scrape_club_data_and_save_to_database(url), timeout=2) for url in club_page_urls]
                await asyncio.gather(*tasks)
            except Exception as e:
                logger.error("Failed to update teams", extra={"tags": ["exception"], "error": traceback.format_exc()})

        asyncio.run(coro())

    def update_matches_model(self):
        from model.scrapers.match_data_scraper import MatchDataScraper
        from model.scrapers.match_urls_scraper import MatchUrlsScraper

        configure_logger(resolve_class_module_name(MatchUrlsScraper))
        configure_logger(resolve_class_module_name(MatchDataScraper))

        database_model = ModelFactory.create_model('matches')

        async def coro():
            try:
                match_urls_scraper = MatchUrlsScraper()
                await match_urls_scraper.initialize()
                match_page_urls = await match_urls_scraper.get_match_urls()
                logger.debug("Match URLs fetched", extra={"tags": ["network"], "destination": "match_urls_source", "method": "GET"})

                async def scrape_match_data_and_save_to_database(url):
                    match_scraper = MatchDataScraper()
                    await match_scraper.initialize()
                    match_data = await match_scraper.get_all_data()
                    try:
                        database_model.creat_record(match_data)
                        logger.info("Match data inserted", extra={"tags": ["event", "access"], "resource": "matches"})
                    except IntegrityError:
                        database_model.update_record(match_data)
                        logger.warning("Match data updated after IntegrityError", extra={"tags": ["warning"], "resource": "matches"})

                await asyncio.gather(*(scrape_match_data_and_save_to_database(url) for url in match_page_urls))
            except Exception:
                logger.error("Failed to update matches", extra={"tags": ["exception"], "error": traceback.format_exc()})

        asyncio.run(coro())

    def update_players_model(self):
        from model.scrapers.player_data_scraper import PlayerDataScraper
        from model.scrapers.player_urls_scraper import PlayerUrlsScraper
        from model.scrapers.club_urls_scraper import ClubUrlsScraper

        configure_logger(resolve_class_module_name(ClubUrlsScraper))
        configure_logger(resolve_class_module_name(PlayerDataScraper))
        configure_logger(resolve_class_module_name(PlayerUrlsScraper))

        database_model = ModelFactory.create_model('players')

        async def coro():
            try:
                club_urls_scraper = ClubUrlsScraper()
                await club_urls_scraper.initialize()
                club_page_urls = await club_urls_scraper.get_club_urls()
                logger.debug("Club URLs for players fetched", extra={"tags": ["network"], "destination": "club_urls_source", "method": "GET"})
                club_page_urls = club_page_urls[1:]

                async def scrape_club_players(club_url):
                    player_urls_scraper = PlayerUrlsScraper(club_url)
                    await player_urls_scraper.initialize()
                    club_player_urls = await player_urls_scraper.get_club_player_urls()
                    club_player_urls = club_player_urls[1:]

                    async def scrape_player_data(player_url):
                        player_scraper = PlayerDataScraper(player_url)
                        await player_scraper.initialize()
                        player_data = player_scraper.get_all_data()
                        try:
                            database_model.creat_record(player_data)
                            logger.info("Player data inserted", extra={"tags": ["event", "access"], "resource": "players"})
                        except IntegrityError:
                            database_model.update_record(player_data)
                            logger.warning("Player data updated after IntegrityError", extra={"tags": ["warning"], "resource": "players"})

                    await asyncio.gather(*(scrape_player_data(url) for url in club_player_urls))

                await asyncio.gather(*(scrape_club_players(url) for url in club_page_urls))
            except Exception:
                logger.error("Failed to update players", extra={"tags": ["exception"], "error": traceback.format_exc()})

        asyncio.run(coro())

    def update_tables_model(self):
        from model.scrapers.tables_data_scraper import TablesDataScraper

        configure_logger(resolve_class_module_name(TablesDataScraper))

        database_model = ModelFactory.create_model('tables')

        async def coro():
            try:
                scraper = TablesDataScraper()
                await scraper.initialize()
                tables_data = await scraper.get_tables_data()
                for standing in tables_data:
                    try:
                        database_model.create_record(standing)
                        logger.info("Table data inserted", extra={"tags": ["event", "access"], "resource": "tables"})
                    except Exception as e:
                        database_model.update_record(standing)
                        logger.warning("Table data updated after insertion error", extra={"tags": ["warning"], "error": str(e), "resource": "tables"})
            except Exception as e:
                logger.error("Failed to update tables", extra={"tags": ["exception"], "error": traceback.format_exc()})

        asyncio.run(coro())

class ScrapeDataCommand(ICommand): 
    base_name = 'scrape'
    description = 'scrape data with scraper and display in terminal'

    def __init__(self, *args):
        logger.debug("Initializing ScrapeDataCommand", extra={"tags": ["debug", "event"], "args": args})
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
        logger.debug("Scraper type and arguments set", extra={"tags": ["debug"], "scraper_type": self._type, "scraper_args": self._arguments})

        try:
            self._scraper = self.SCRAPE_REGISTERY[self._type](*self._arguments)
        except KeyError as e:
            logger.error("Invalid scraper type", extra={"tags": ["validation", "exception"], "field": "scraper_type", "value": self._type, "error": str(e)})
            raise

        self._printer = ScrapeDataCommand.Printer

    def execute_command(self):
        logger.info("Executing scrape command", extra={"tags": ["event", "access"], "action": "scrape", "resource": self._type})
        try:
            data = self._scraper.scrape_data()
            logger.info("Scraping completed", extra={"tags": ["event"], "event_type": "data_scraped", "scraper_type": self._type})
        except Exception as e:
            logger.error("Scraping failed", extra={"tags": ["exception"], "error": traceback.format_exc()})
            raise

        self._printer.print_data(data)

        while True:
            print("\n1. Done\n2. save the data\n")
            choice = input("=> ")

            if choice == "1":
                logger.info("User chose to exit without saving", extra={"tags": ["event", "access"], "action": "exit", "resource": self._type})
                break
            elif choice == "2":
                destination = self._choose_destination()
                file_name = self._type + self.get_date_string_for_filename()
                logger.info("Saving scraped data", extra={"tags": ["event", "access"], "action": "save_data", "resource": file_name})
                ScrapeDataCommand.DataExporter.export_data(data, file_name, destination)
                break

    def get_date_string_for_filename(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def _choose_destination(self) -> str:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()

        folder_selected = filedialog.askdirectory(title="Select Destination Folder")
        logger.debug("Destination folder selected", extra={"tags": ["debug", "access"], "resource": folder_selected})
        return folder_selected

    class IScraper(ABC):
        @abstractmethod
        def scrape_data(self) -> list[tuple]: pass

        @abstractmethod
        def _validate_arguments(self, *args): pass

    class ClubUrlsScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)

        def scrape_data(self):
            return asyncio.run(self._main())

        def _validate_arguments(self, *args):
            logger.debug("Validating arguments for ClubUrlsScraper", extra={"tags": ["debug", "validation"], "args": args})

        async def _main(self):
            from model.scrapers.club_urls_scraper import ClubUrlsScraper

            configure_logger(resolve_class_module_name(ClubUrlsScraper))

            scraper = ClubUrlsScraper()
            await scraper.initialize()
            result = await scraper.get_club_urls()
            logger.info("Club URLs scraped", extra={"tags": ["event", "network"], "event_type": "club_urls_scraped"})
            return result

    class ClubDataScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)
            self.arguments = args

        def scrape_data(self):
            try:
                result = asyncio.run(self._main())
                logger.info("Club data scraped successfully", extra={"tags": ["event"], "event_type": "club_data_scraped"})
                return result
            except Exception as e:
                logger.error("Error scraping club data", extra={"tags": ["exception"], "error": traceback.format_exc()})
                raise

        def _validate_arguments(self, *args):
            if not args:
                logger.warning("Validation failed: no arguments provided", extra={"tags": ["validation", "warning"], "field": "args", "value": args, "result": "failed"})
                raise ValueError('no club urls provided!')
            logger.debug("Arguments validated for ClubDataScraper", extra={"tags": ["validation"], "field": "args", "value": args, "result": "passed"})

        async def _main(self):
            from model.scrapers.club_data_scraper import ClubDataScraper

            configure_logger(resolve_class_module_name(ClubDataScraper))

            tasks = []
            for url in self.arguments:
                scraper = ClubDataScraper(url)
                await scraper.initialize()
                tasks.append(scraper.get_all_data())
            result = await asyncio.gather(*tasks)
            return result
        
    class MatchUrlsScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)

        def scrape_data(self):
            logger.debug("Starting scrape_data in MatchUrlsScraper", extra={"tags": ["debug"]})
            result = asyncio.run(self._main())
            logger.debug("Completed scrape_data in MatchUrlsScraper", extra={"tags": ["debug"]})
            return result

        async def _main(self):
            from model.scrapers.match_urls_scraper import MatchUrlsScraper

            configure_logger(resolve_class_module_name(MatchUrlsScraper))

            scraper = MatchUrlsScraper()
            await scraper.initialize()
            result = await scraper.get_match_urls()
            logger.info("Match URLs scraping completed", extra={"tags": ["event"], "event_type": "data_scraped"})
            return result

        def _validate_arguments(self, *args):
            logger.debug("Validating arguments in MatchUrlsScraper", extra={"tags": ["debug", "validation"], "args": args})
            pass

        def format_data(self, data):
            result = []
            for round, match_urls in data.values():
                for match_url in match_urls:
                    result.append({"url": match_url,"round": round})
            logger.debug("Formatted match URLs data", extra={"tags": ["debug"]})
            return result

    class MatchDataScraper(IScraper):
        def __init__(self, *args):
            self._validate_arguments(*args)
            self.match_urls = args
            logger.debug("Initialized MatchDataScraper", extra={"tags": ["debug"], "match_urls": args})

        def scrape_data(self):
            logger.debug("Starting scrape_data in MatchDataScraper", extra={"tags": ["debug"]})
            result = asyncio.run(self._main())
            logger.debug("Completed scrape_data in MatchDataScraper", extra={"tags": ["debug"]})
            return result

        async def _main(self):
            from model.scrapers.match_data_scraper import MatchDataScraper

            configure_logger(resolve_class_module_name(MatchDataScraper))

            tasks = []

            for match_url in self.match_urls:
                scraper = MatchDataScraper(match_url)
                await scraper.initialize()
                logger.debug("Initialized MatchDataScraper instance", extra={"tags": ["debug", "network"], "destination": match_url})
                tasks.append(scraper.get_all_data())

            result = await asyncio.gather(*tasks)

            logger.info("Match data scraping completed", extra={"tags": ["event"], "event_type": "data_scraped"})
            return result

        def _validate_arguments(self, *args):
            if not args:
                logger.warning("No match URLs provided", extra={"tags": ["warning", "validation"], "field": "match_urls", "value": args, "result": "failed"})
                raise ValueError('no match urls provided!')
            
    class PlayerUrlsScraper(IScraper):
        def __init__(self, *args):
            logger.debug("Initializing PlayerUrlsScraper", extra={"tags": ["debug", "event"], "args": args})
            self._validate_arguments(*args)
            self.type = args[0]
            self.arguments = args[1:]

        def scrape_data(self):
            return asyncio.run(self._main())

        async def _main(self):
            from model.scrapers.player_urls_scraper import PlayerUrlsScraper

            configure_logger(resolve_class_module_name(PlayerUrlsScraper))

            tasks = []
            for argument in self.arguments:
                if self.type == 'name':
                    scraper = PlayerUrlsScraper(club_name=argument)
                elif self.type == 'url':
                    scraper = PlayerUrlsScraper(url=argument)
                await scraper.initialize()
                logger.debug("Initialized player URL scraper", extra={"tags": ["debug", "network"], "destination": argument})
                tasks.append(scraper.get_club_player_urls())

            result = await asyncio.gather(*tasks)
            logger.info("Completed player URL scraping", extra={"tags": ["event"], "event_type": "player_urls_scraped"})
            return result

        def _validate_arguments(self, *args):
            type = args[0] if args else None
            if not type:
                logger.warning("Validation failed: no input type", extra={"tags": ["validation"], "field": "type", "value": type, "result": "failed"})
                raise ValueError('no input type provided!\ntypes supported: url, name')
            elif type not in ('name', 'url'):
                logger.warning("Validation failed: invalid input type", extra={"tags": ["validation"], "field": "type", "value": type, "result": "failed"})
                raise ValueError('input type provided is not valid!')
            if not args[1:]:
                logger.warning("Validation failed: missing secondary args", extra={"tags": ["validation"], "field": "args", "value": args, "result": "failed"})
                raise ValueError(f'no {"club name" if type == "name" else type} provided!')

        def format_data(self, data: list[dict]) -> list[tuple]:
            for record in data:
                record.pop('picture')
            logger.debug("Formatted player data", extra={"tags": ["debug"]})
            return data

    class PlayerDataScraper(IScraper):
        def __init__(self, *args):
            logger.debug("Initializing PlayerDataScraper", extra={"tags": ["debug", "event"], "args": args})
            self._validate_arguments(*args)
            self.urls = args

        def scrape_data(self):
            return asyncio.run(self._main())

        async def _main(self):
            from model.scrapers.player_data_scraper import PlayerDataScraper

            configure_logger(resolve_class_module_name(PlayerDataScraper))

            tasks = []
            for player_page_url in self.urls:
                scraper = PlayerDataScraper(player_page_url)
                await scraper.initialize()
                logger.debug("Initialized PlayerDataScraper", extra={"tags": ["debug", "network"], "destination": player_page_url})
                tasks.append(scraper.get_all_data())

            result = await asyncio.gather(*tasks)
            logger.info("Player data scraping completed", extra={"tags": ["event"], "event_type": "player_data_scraped"})
            return result

        def _validate_arguments(self, *args):
            if not args:
                logger.warning("Validation failed: no player URLs provided", extra={"tags": ["validation"], "field": "urls", "value": args, "result": "failed"})
                raise ValueError('no player page url provided!')

    class TablesDataScraper(IScraper):
        def __init__(self, *args):
            logger.debug("Initializing TablesDataScraper", extra={"tags": ["debug", "event"], "args": args})
            self._validate_arguments(*args)

        def scrape_data(self):
            return asyncio.run(self._main())

        async def _main(self):
            from model.scrapers.tables_data_scraper import TablesDataScraper

            configure_logger(resolve_class_module_name(TablesDataScraper))

            scraper = TablesDataScraper()
            await scraper.initialize()
            logger.debug("Initialized TablesDataScraper", extra={"tags": ["debug", "network"]})
            result = await scraper.get_tables_data()
            logger.info("Tables data scraping completed", extra={"tags": ["event"], "event_type": "tables_data_scraped"})
            return result 

        def _validate_arguments(self, *args):
            pass

    class Printer:
        @staticmethod
        def print_data(data):
            import pandas as pd

            pd.set_option('display.max_colwidth', None)
            pd.set_option('display.width', None)
            pd.set_option('display.expand_frame_repr', False)

            columns = tuple(data[0].keys())
            data = [tuple(record.values()) for record in data]

            data_frame = pd.DataFrame(data, columns=columns)
            logger.debug("Displaying data in terminal", extra={"tags": ["access"], "resource": "stdout", "columns": columns})
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
        from controller import tests_controller

        configure_logger(tests_controller.__name__)

        logger.info("Executing tests controller program", extra={
                "tags": ["event", "access"],
                "event_type": "execute_program",
            })
        try:
            tests_controller.main()
            logger.info("tests controller program executed successfully", extra={
                "tags": ["event"],
                "event_type": "test_execution_complete"
            })
        except Exception as e:
            logger.error("error raised during executing tests controller program", extra={
                "tags": ["exception", "error"],
                "error": traceback.format_exc(),
            })
            raise


class TestRequestHandler(ICommand):
    base_name = 'test_request_handler'
    description = 'provide some urls as argument so handler will serve them gracefully and return a chunk of reponses as proof'

    def __init__(self, *args):
        logger.debug("Initializing TestRequestHandler", extra={
            "tags": ["debug", "event"],
            "args": args
        })
        if not args:
            logger.error("No URL argument provided to TestRequestHandler", extra={
                "tags": ["validation", "exception"],
                "field": "args",
                "value": args
            })
            raise ValueError('no url provided!')

        self.arguments = args
        logger.info("TestRequestHandler initialized with URLs", extra={
            "tags": ["event"],
            "event_type": "init_handler",
            "resource": "RequestHandler",
            "value": args
        })

    def execute_command(self):
        logger.info("Starting async request test execution", extra={
            "tags": ["event"],
            "event_type": "execute_command"
        })
        asyncio.run(self._main())

    async def _main(self):
        from model.scrapers.request_handler import RequestHandler

        configure_logger(resolve_class_module_name(RequestHandler))

        try:
            handler = RequestHandler()
            logger.debug("RequestHandler instance created", extra={
                "tags": ["debug"]
            })

            await handler.configure()
            logger.info("RequestHandler configured", extra={
                "tags": ["event"],
                "event_type": "configure_handler"
            })

            tasks = [handler.get(url) for url in self.arguments]

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            duration = round(time.time() - start_time, 2)

            logger.info("All requests completed", extra={
                "tags": ["event", "network"],
                "event_type": "request_complete",
                "latency": duration,
                "action": "fetch",
                "resource": self.arguments
            })

            for i, result in enumerate(results, 1):
                print(f"\n--- Result {i} ---\n{result[:500]}...\n")

        except Exception as e:
            logger.critical("Unhandled error in request handler execution", extra={
                "tags": ["critical", "exception"],
                "error": traceback.format_exc()
            })
            print(f"Error occurred: {e}")