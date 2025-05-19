import datetime, io, binascii, webbrowser
from model.model_factory import ModelFactory
from view import program_view
from PIL import Image, ImageTk

class MainController:
    def get_matches_section_callback(self):
        return MatchesSectionController()
    
    def get_tables_section_callback(self):
        return TablesSectionController()
    
    def get_teams_section_callback(self):
        return TeamsSectionController()
    
    def get_players_section_callback():
        return PlayersSectionController()

class MatchesSectionController:
    def __init__(self):
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')
        self.matches_database_controller = ModelFactory.create_model(table_name='matches')

    def _prepare_team_logos(self, width):
        team_logo_binary_datas = self.teams_database_controller.get_specific_column(column="logo", key="name")
        return {team_name: ImageManager.create_image_object(logo_data, width) for team_name, logo_data in team_logo_binary_datas.items()}
        
    def _get_team_names(self):
        return self.teams_database_controller.get_specific_column(column='name', key='id')

    def get_weeks_count(self):
        teams_count = self.teams_database_controller.get_records_count()
        weeks_count = 2 * (teams_count - 1)
        return weeks_count

    def get_this_week_number(self):
        timestamps = self.matches_database_controller.get_specific_column('timestamp', 'id')

        nearest_id = self.find_nearest_id(timestamps)
        
        nearest_record = self.matches_database_controller.get_records(id=nearest_id) 
        this_week_number = nearest_record['week_number']
        
        return this_week_number
    
    def _find_nearest_id(self, timestamps: dict[int: int]):
        nearest_id = timestamps.keys()[0]
        now_timestamp = datetime.datetime.now()
        lowest_remained_time = timestamps[nearest_id] - now_timestamp

        for id, timestamp in timestamps.items():
            remained_time = timestamp - now_timestamp

            if remained_time > 0 and remained_time < lowest_remained_time:
                nearest_id = id
        
        return nearest_id

    def get_week_data(self, week_number, logos_width=35):
        data = self.matches_database_controller.get_records(week=week_number)
        data = WeekDataFormatter.format_data(data, self._get_team_names(), self._prepare_team_logos(logos_width))
        return data

class TablesSectionController:
    def __init__(self):
        self.tables_database_controller = ModelFactory.create_model(table_name='tables')
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')

    def _get_team_names(self):
        team_names = self.teams_database_controller.get_specific_column(column='team_name', key='id')
        return team_names

    def _prepare_team_logos(self, width):
        team_logo_binary_datas = self.teams_database_controller.get_specific_column(column='logo', key='team_name')
        team_logos = {team_name: ImageManager.create_image_object(logo_data, width) for team_name, logo_data in team_logo_binary_datas.items()}

        return team_logos
    def get_tables_data(self, logos_width=35):
        tables_data_dict = self.tables_database_controller.get_records()
        tables_data_dict = TablesDataFormatter.format_data(tables_data_dict, self._get_team_names() , self._prepare_team_logos(width=logos_width))
        return tables_data_dict

class TeamsSectionController:
    def __init__(self):
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')

    def get_teams_data(self, logos_width):
        data = self.teams_database_controller.get_records()
        data = TeamsDataFormatter.format_data(data, logos_width)
        return data

class PlayersSectionController:
    def __init__(self):
        self.player_database_controller = ModelFactory.create_model(table_name='players')
        self.teams_database_controller = ModelFactory.create_model(table_name='teams')

    def get_players_data(self, team_name, picture_width):
        team_players = self.teams_database_controller.get_records(team_name=team_name)
        team_players = TeamsDataFormatter.format_data(team_players, picture_width)
        return team_players
    
    def get_teams_data(self, logos_width):
        team_logos = self.teams_database_controller.get_specific_column(column='logo', key='name')

        teams_list = [{'team_name':team_name, 'team_logo':team_logo} for team_name, team_logo in team_logos.items()]

        return teams_list

class WeekDataFormatter():
    @staticmethod
    def format_data(data, team_names, team_logos):
        sorted_data_dict = dict()
        
        for match_record in data:
            home_team_name = team_names[match_record['home_team_id']]
            match_record['home_team_data']['team_name'] = home_team_name
            match_record['home_team_data']['logo'] = team_logos[home_team_name]

            away_team_name = team_names[match_record['away_team_id']]
            match_record['away_team_data']['team_name'] = away_team_name
            match_record['away_team_data']['logo'] = team_logos[away_team_name]

            match_date_object = datetime.datetime.fromtimestamp(match_record['timestamp'])
            match_date_string = match_date_object.strftime('%a %d/%m/%Y')
            
            if match_date_string not in data.keys():
                sorted_data_dict[match_date_string] = list()

            sorted_data_dict[match_date_string].append(match_record)

        return sorted_data_dict
    
class TeamsDataFormatter:
    @staticmethod
    def format_data(data, logos_width):
        return data

class TablesDataFormatter:
    @staticmethod
    def format_data(data, team_names, team_logos):
        return data

class PlayersDataFormatter:
    @staticmethod
    def format_data(data, pictures_width):
        sorted_dict = dict()

        for player in data:
            player['picture'] = ImageManager.create_image_object(player['picture'], pictures_width=pictures_width)

            sorted_dict[player['position']] = player

        return data

class ImageEditor:
    @staticmethod
    def resize_image_with_width(image: Image, width: int):
        image_width, image_height = image.size
        image_ratio = image_width / image_height
        new_image_width = width
        new_image_height = int(new_image_width / image_ratio)

        image = image.resize((new_image_width, new_image_height))
        return image

class ImageManager():
    @staticmethod
    def create_image_object(image_data, image_width):
        image_file_object = io.BytesIO(binascii.unhexlify(image_data))
        image_object = Image.open(image_file_object)
        image_object = ImageEditor.resize_image_with_width(image=image_object, width=image_width)
        image_object = ImageTk.PhotoImage(image_object)
        return image_object