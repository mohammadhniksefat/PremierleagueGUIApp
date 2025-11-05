import pytest, tkinter, sys, os, json, datetime, io, binascii, webbrowser
from unittest.mock import MagicMock
from tkinter import ttk 
from pathlib import Path
import os, copy

from premierleague.tests.utils import prepare_image, resize_image_with_width
from PIL import Image, ImageTk
from premierleague.view import program_view
from premierleague.view.program_view import TablesSection
from premierleague.view.program_view import TeamsSection
from premierleague.view.program_view import MatchesSection
from premierleague.view.program_view import PlayersSection

from premierleague.view.matches_section import MatchesSection
from premierleague.view.tables_section import TablesSection
from premierleague.view.teams_section import TeamsSection
from premierleague.view.players_section import PlayersSection


FIXTURES_FOLDER_PATH = str(Path(os.path.dirname(__file__)).parent / 'fixtures')

def get_teams_mocked_database():
    json_file_path = FIXTURES_FOLDER_PATH + os.sep + 'mock_teams_data.json'
    
    with open(json_file_path) as json_file:
        mock_database = json.load(json_file)
    
    return copy.deepcopy(mock_database)

def get_matches_mocked_database():
    json_file_path = FIXTURES_FOLDER_PATH + os.sep + 'mock_matches_data.json'
    
    with open(json_file_path) as json_file:
        mock_database = json.load(json_file)

    return copy.deepcopy(mock_database)

def get_tables_mocked_database():
    json_file_path = FIXTURES_FOLDER_PATH + os.sep + 'mock_tables_data.json'
    
    with open(json_file_path) as json_file:
        mock_database = json.load(json_file)

    return copy.deepcopy(mock_database)

def get_players_mocked_database():
    json_file_path = FIXTURES_FOLDER_PATH + os.sep + 'mock_players_data.json'
    
    with open(json_file_path) as json_file:
        mock_database = json.load(json_file)

    return copy.deepcopy(mock_database)

def test_program_window_preparation(mocker):    
    matches_class = MatchesSection
    tables_class = TablesSection
    teams_class = TeamsSection
    players_class = PlayersSection

    def mock_section(section_name):

        def method(*args, **kwargs):
            nonlocal section_name
            
            master = args[0]

            if section_name == 'matches_section':
                section = get_matches_section(get_matches_mocked_database(), get_teams_mocked_database(), master, cls=matches_class)
            elif section_name == 'tables_section':
                section = get_tables_section(get_tables_mocked_database(), get_teams_mocked_database(), master, cls=tables_class)
            elif section_name == 'teams_section':
                section = get_teams_section(get_teams_mocked_database(), master, cls=teams_class)
            elif section_name == 'players_section':
                section = get_players_section(get_players_mocked_database(), get_teams_mocked_database(), master, cls=players_class)

            return section

        return method

    mocker.patch("premierleague.view.program_view.MatchesSection", side_effect=mock_section('matches_section'))
    mocker.patch("premierleague.view.program_view.TablesSection", side_effect=mock_section('tables_section'))
    mocker.patch("premierleague.view.program_view.TeamsSection", side_effect=mock_section('teams_section'))
    mocker.patch("premierleague.view.program_view.PlayersSection", side_effect=mock_section('players_section'))

    mock_callback = MagicMock()

    program_window = program_view.ProgramWindow(mock_callback)
    program_window.display()

def test_matches_section_view():
    matches_mocked_database = get_matches_mocked_database()
    teams_mocked_database = get_teams_mocked_database()
    
    container = tkinter.Tk()
    container.geometry('400x500')
    
    section = get_matches_section(matches_mocked_database, teams_mocked_database, container)
    section.widget.pack(fill='both', expand=True)

    container.mainloop()

def test_tables_section_view():
    tables_mocked_database = get_tables_mocked_database()
    teams_mocked_database = get_teams_mocked_database()

    container = tkinter.Tk()
    container.resizable(False, True)

    section = get_tables_section(tables_mocked_database, teams_mocked_database, container)
    section.widget.pack(fill='both', expand=True)

    container.mainloop()


def test_teams_section_view():
    teams_mocked_database = get_teams_mocked_database()

    container = tkinter.Tk()

    section = get_teams_section(teams_mocked_database, container)
    section.widget.pack(fill='both', expand=True)

    container.mainloop()


def test_players_section_view(): 
    players_mocked_database = get_players_mocked_database()
    teams_mocked_database = get_teams_mocked_database()

    container = tkinter.Tk()

    section = get_players_section(players_mocked_database, teams_mocked_database, container)
    section.widget.pack(fill='both', expand=True)

    container.mainloop()


def get_matches_section(matches_mocked_database, teams_mocked_database, container, cls=None):
    team_names = {record['id'] : record['team_name'] for record in teams_mocked_database}
    team_logos = dict()

    def mock_get_week_data(*args, logos_width=35, **kwargs):
        nonlocal matches_mocked_database, team_names, team_logos

        for record in teams_mocked_database:
            team_logos[record['team_name']] = prepare_image(record['logo'], logos_width)

        week_number = args[0]
        filtered_data_dict = list(filter(lambda week_data: True if week_data["week_number"] == week_number else False, matches_mocked_database))
        sorted_data_dict = dict()

        for match_record in filtered_data_dict:
            home_team_name = team_names[match_record['home_team_id']]
            match_record['home_team_data']['team_name'] = home_team_name
            match_record['home_team_data']['logo'] = team_logos[home_team_name]

            away_team_name = team_names[match_record['away_team_id']]
            match_record['away_team_data']['team_name'] = away_team_name
            match_record['away_team_data']['logo'] = team_logos[away_team_name]

            match_date_object = datetime.datetime.fromtimestamp(match_record['timestamp'])
            match_date_string = match_date_object.strftime('%a %d/%m/%Y')
            
            if match_date_string not in sorted_data_dict.keys():
                sorted_data_dict[match_date_string] = list()

            sorted_data_dict[match_date_string].append(match_record)

        return sorted_data_dict

    mock_callback = MagicMock()
    mock_callback.get_weeks_count.return_value = 6
    mock_callback.get_this_week_number.return_value = 3
    mock_callback.get_week_data = mock_get_week_data

    section = MatchesSection(container, mock_callback) if not cls else cls(container, mock_callback)

    return section


def get_tables_section(tables_mocked_database, teams_mocked_database, container, cls=None):
    def mock_get_tables_data(logos_width=25, *args, **kwargs):
        team_logos = {record['id']:record['logo'] for record in teams_mocked_database}
        for record in tables_mocked_database:
            team_logo_data = team_logos[record['team_id']]
            record['team_logo'] = prepare_image(team_logo_data, logos_width)
        
        tables_mocked_database.sort(key=lambda record: record['points'], reverse=True)
        return tables_mocked_database

    mock_tables_callback = MagicMock()
    mock_tables_callback.get_tables_data = mock_get_tables_data

    section = TablesSection(container=container, callback=mock_tables_callback) if not cls else cls(container=container, callback=mock_tables_callback)

    return section

def get_teams_section(teams_mocked_database, container, cls=None):    
    def mock_get_teams_data(logos_width):
        for record in teams_mocked_database:
            record['logo'] = prepare_image(image_data=record['logo'], width=logos_width)

        return teams_mocked_database

    mock_teams_section_callback = MagicMock()
    mock_teams_section_callback.get_teams_data = mock_get_teams_data

    section = TeamsSection(container=container, callback=mock_teams_section_callback) if not cls else cls(container=container, callback=mock_teams_section_callback)

    return section

def get_players_section(players_mocked_database, teams_mocked_database, container, cls=None):    
    def mock_get_players_data(team_name, player_picture_width):
        nonlocal players_mocked_database, teams_mocked_database

        team_id = {record['team_name'] : record['id'] for record in teams_mocked_database}[team_name]
        
        team_players = list(filter(lambda record: record['team'] == team_id, players_mocked_database))

        sorted_dict = dict()

        for player in team_players:
            player['player_picture'] = prepare_image(player['player_picture'], width=player_picture_width)
            
            if player['position'] not in sorted_dict.keys():
                sorted_dict[player['position']] = list()
                
            sorted_dict[player['position']].append(player)
        
        return sorted_dict
    
    def mock_get_teams_data(logos_width):
        nonlocal teams_mocked_database

        teams_list = [{"team_name":record["team_name"], "team_logo":prepare_image(record["logo"], logos_width)} for record in teams_mocked_database]
        return teams_list
    
    mock_players_callback = MagicMock()
    mock_players_callback.get_players_data = mock_get_players_data
    mock_players_callback.get_teams_data = mock_get_teams_data

    section = PlayersSection(container=container, callback=mock_players_callback) if not cls else cls(container=container, callback=mock_players_callback)
    
    return section