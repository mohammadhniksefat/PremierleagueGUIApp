import datetime
import io
import binascii
import webbrowser
import logging
import json
import traceback
from PIL import Image, ImageTk
from model.model_factory import ModelFactory
from view import program_view
from log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(program_view.__name__)
configure_logger(resolve_class_module_name(ModelFactory))

class MainController:
    def get_matches_section_callback(self):
        logger.info("Matches section controller callback invoked", extra={"extra": {"tags": ["event", "ui"], "event_type": "controller_callback"}})
        return MatchesSectionController()
    
    def get_tables_section_callback(self):
        logger.info("Tables section controller callback invoked", extra={"extra": {"tags": ["event", "ui"], "event_type": "controller_callback"}})
        return TablesSectionController()
    
    def get_teams_section_callback(self):
        logger.info("Teams section controller callback invoked", extra={"extra": {"tags": ["event", "ui"], "event_type": "controller_callback"}})
        return TeamsSectionController()
    
    def get_players_section_callback(self):
        logger.info("Players section controller callback invoked", extra={"extra": {"tags": ["event", "ui"], "event_type": "controller_callback"}})
        return PlayersSectionController()

class MatchesSectionController:
    def __init__(self):
        logger.info("Initializing MatchesSectionController", extra={"extra": {"tags": ["init", "db"], "event_type": "controller_init"}})
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')
        self.matches_database_controller = ModelFactory.create_model(table_name='matches')

    def _prepare_team_logos(self, width):
        logger.debug("Preparing team logos", extra={"extra": {"tags": ["debug", "image"], "field": "logo", "value": width}})
        team_logo_binary_datas = self.teams_database_controller.get_specific_column(column="logo", key="name")
        return {
            team_name: ImageManager.create_image_object(logo_data, width)
            for team_name, logo_data in team_logo_binary_datas.items()
        }

    def _get_team_names(self):
        logger.debug("Fetching team names from database", extra={"extra": {"tags": ["debug", "db"], "resource": "teams", "action": "get_names"}})
        return self.teams_database_controller.get_specific_column(column='name', key='id')

    def get_weeks_count(self):
        logger.info("Calculating total weeks", extra={"extra": {"tags": ["event", "calculation"], "event_type": "get_weeks_count"}})
        teams_count = self.teams_database_controller.get_records_count()
        weeks_count = 2 * (teams_count - 1)
        logger.debug("Computed weeks", extra={"extra": {"tags": ["debug"], "field": "weeks_count", "value": weeks_count}})
        return weeks_count

    def get_this_week_number(self):
        logger.info("Getting this week's number", extra={"extra": {"tags": ["event", "data"], "event_type": "get_current_week"}})
        try:
            timestamps = self.matches_database_controller.get_specific_column('timestamp', 'id')
            nearest_id = self._find_nearest_id(timestamps)
            nearest_record = self.matches_database_controller.get_records(id=nearest_id)
            this_week_number = nearest_record['week_number']
            logger.debug("Identified current week", extra={"extra": {"tags": ["debug"], "field": "week_number", "value": this_week_number}})
            return this_week_number
        except Exception as e:
            logger.error("Failed to get this week's number", extra={
                "extra": {
                    "tags": ["exception", "db"],
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            })
            raise

    def _find_nearest_id(self, timestamps: dict):
        now_timestamp = datetime.datetime.now().timestamp()
        logger.debug("Finding nearest ID by timestamp", extra={"extra": {"tags": ["debug", "time"], "field": "now_timestamp", "value": now_timestamp}})
        nearest_id = list(timestamps.keys())[0]
        lowest_remained_time = float('inf')

        for id, timestamp in timestamps.items():
            remained_time = timestamp - now_timestamp
            if 0 < remained_time < lowest_remained_time:
                nearest_id = id
                lowest_remained_time = remained_time

        logger.debug("Nearest match ID found", extra={"extra": {"tags": ["debug"], "field": "nearest_id", "value": nearest_id}})
        return nearest_id

    def get_week_data(self, week_number, logos_width=35):
        logger.info("Fetching week data", extra={"extra": {"tags": ["event", "data"], "field": "week_number", "value": week_number}})
        raw_data = self.matches_database_controller.get_records(match_week=week_number)
        formatted_data = WeekDataFormatter.format_data(raw_data, self._get_team_names(), self._prepare_team_logos(logos_width))
        return formatted_data

class TablesSectionController:
    def __init__(self):
        logger.info("Initializing TablesSectionController", extra={"extra": {"tags": ["init", "db"], "event_type": "controller_init"}})
        self.tables_database_controller = ModelFactory.create_model(table_name='tables')
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')

    def _get_team_names(self):
        logger.debug("Getting team names from DB", extra={"extra": {"tags": ["debug", "db"], "field": "team_name"}})
        return self.teams_database_controller.get_specific_column(column='team_name', key='id')

    def _prepare_team_logos(self, width):
        logger.debug("Preparing team logos", extra={"extra": {"tags": ["debug", "image"], "field": "logo", "value": width}})
        raw_logos = self.teams_database_controller.get_specific_column(column='logo', key='team_name')
        return {
            team_name: ImageManager.create_image_object(logo_data, width)
            for team_name, logo_data in raw_logos.items()
        }

    def get_tables_data(self, logos_width=35):
        logger.info("Retrieving tables data", extra={"extra": {"tags": ["event", "data"], "event_type": "get_tables_data"}})
        raw = self.tables_database_controller.get_records()
        formatted = TablesDataFormatter.format_data(raw, self._get_team_names(), self._prepare_team_logos(width=logos_width))
        return formatted

class TeamsSectionController:
    def __init__(self):
        logger.info("Initializing TeamsSectionController", extra={"extra": {"tags": ["init", "db"], "event_type": "controller_init"}})
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')

    def get_teams_data(self, logos_width):
        logger.info("Fetching teams data", extra={"extra": {"tags": ["event", "data"], "resource": "teams", "action": "get_all"}})
        raw = self.teams_database_controller.get_records()
        return TeamsDataFormatter.format_data(raw, logos_width)

class PlayersSectionController:
    def __init__(self):
        logger.info("Initializing PlayersSectionController", extra={"extra": {"tags": ["init", "db"], "event_type": "controller_init"}})
        self.player_database_controller = ModelFactory.create_model(table_name='players')
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')

    def get_players_data(self, team_name, picture_width):
        logger.info("Fetching players for team", extra={"extra": {"tags": ["event", "data", "access"], "resource": "players", "action": "get_by_team", "field": "team_name", "value": team_name}})
        data = self.teams_database_controller.get_records(team_name=team_name)
        return TeamsDataFormatter.format_data(data, picture_width)

    def get_teams_data(self, logos_width):
        logger.info("Fetching team logos", extra={"extra": {"tags": ["event", "data"], "resource": "teams", "action": "get_logos"}})
        team_logos = self.teams_database_controller.get_specific_column(column='logo', key='name')
        teams_list = [{'team_name': name, 'team_logo': logo} for name, logo in team_logos.items()]
        return teams_list
    
class WeekDataFormatter:
    @staticmethod
    def format_data(data, team_names, team_logos):
        logger.info("Formatting week match data", extra={
            "extra": {"tags": ["event", "data"], "event_type": "format_week_data"}
        })

        sorted_data_dict = dict()

        for match_record in data:
            try:
                home_team_name = team_names[match_record['home_team_id']]
                away_team_name = team_names[match_record['away_team_id']]

                match_record['home_team_data']['team_name'] = home_team_name
                match_record['home_team_data']['logo'] = team_logos[home_team_name]
                match_record['away_team_data']['team_name'] = away_team_name
                match_record['away_team_data']['logo'] = team_logos[away_team_name]

                logger.debug("Match record updated with team names and logos", extra={
                    "extra": {
                        "tags": ["debug", "data"],
                        "field": "match_record",
                        "value": {
                            "home_team": home_team_name,
                            "away_team": away_team_name
                        }
                    }
                })

                match_date_object = datetime.datetime.fromtimestamp(match_record['timestamp'])
                match_date_string = match_date_object.strftime('%a %d/%m/%Y')

                if match_date_string not in sorted_data_dict:
                    sorted_data_dict[match_date_string] = []

                sorted_data_dict[match_date_string].append(match_record)

            except Exception as e:
                logger.error("Failed to format match record", extra={
                    "extra": {
                        "tags": ["exception", "formatting"],
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "field": "match_record"
                    }
                })

        return sorted_data_dict


class TeamsDataFormatter:
    @staticmethod
    def format_data(data, logos_width):
        logger.info("Formatting teams data (pass-through)", extra={
            "extra": {
                "tags": ["event", "data"],
                "event_type": "format_teams_data",
                "field": "logos_width",
                "value": logos_width
            }
        })
        return data


class TablesDataFormatter:
    @staticmethod
    def format_data(data, team_names, team_logos):
        logger.info("Formatting tables data (pass-through)", extra={
            "extra": {
                "tags": ["event", "data"],
                "event_type": "format_tables_data"
            }
        })
        return data


class PlayersDataFormatter:
    @staticmethod
    def format_data(data, pictures_width):
        logger.info("Formatting players data", extra={
            "extra": {
                "tags": ["event", "data"],
                "event_type": "format_players_data",
                "field": "pictures_width",
                "value": pictures_width
            }
        })

        sorted_dict = dict()

        for player in data:
            try:
                player['picture'] = ImageManager.create_image_object(player['picture'], image_width=pictures_width)
                sorted_dict[player['position']] = player

                logger.debug("Player image formatted and position mapped", extra={
                    "extra": {
                        "tags": ["debug", "image"],
                        "field": "position",
                        "value": player['position']
                    }
                })

            except Exception as e:
                logger.error("Failed to process player image", extra={
                    "extra": {
                        "tags": ["exception", "image"],
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "field": "player"
                    }
                })

        return data

# --- IMAGE HANDLING ---

class ImageEditor:
    @staticmethod
    def resize_image_with_width(image: Image, width: int):
        try:
            image_width, image_height = image.size
            image_ratio = image_width / image_height
            new_image_width = width
            new_image_height = int(new_image_width / image_ratio)

            logger.debug("Resizing image", extra={
                "extra": {
                    "tags": ["debug", "image"],
                    "event_type": "resize_image",
                    "field": "target_width",
                    "value": width
                }
            })

            resized_image = image.resize((new_image_width, new_image_height))
            return resized_image

        except Exception as e:
            logger.critical("Image resizing failed", extra={
                "extra": {
                    "tags": ["critical", "image"],
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "field": "image_dimensions"
                }
            })
            raise


class ImageManager():
    @staticmethod
    def create_image_object(image_data, image_width):
        logger.info("Creating image object", extra={
            "extra": {
                "tags": ["event", "image"],
                "event_type": "create_image_object",
                "field": "image_width",
                "value": image_width
            }
        })

        try:
            image_file_object = io.BytesIO(binascii.unhexlify(image_data))
            image_object = Image.open(image_file_object)

            logger.debug("Image loaded from binary", extra={
                "extra": {
                    "tags": ["debug", "image"],
                    "event_type": "load_image",
                }
            })

            image_object = ImageEditor.resize_image_with_width(image=image_object, width=image_width)
            image_object = ImageTk.PhotoImage(image_object)

            logger.debug("Image converted to PhotoImage", extra={
                "extra": {
                    "tags": ["debug", "image"],
                    "event_type": "photo_image_created",
                }
            })

            return image_object

        except Exception as e:
            logger.error("Failed to create image object", extra={
                "extra": {
                    "tags": ["exception", "image"],
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "field": "image_data"
                }
            })
            raise