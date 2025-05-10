import pytest, tkinter, sys, os, json, datetime, io, binascii, webbrowser
from tkinter import ttk 
from PIL import Image, ImageTk
# import view
from view import program_view
from view import tables_section
from view import teams_section
from view import matches_section
from view import players_section
from unittest.mock import MagicMock 

def get_teams_mocked_database():
    json_file_path = r"M:\projects\Python\PremierLeague\tests\mocks_data\mock_teams_data_json.json"
    
    with open(json_file_path) as json_file:
        database_mock = json.load(json_file)
    
    return database_mock

def get_matches_mocked_database():
    json_file_path = r"M:\projects\Python\PremierLeague\tests\mocks_data\mock_matches_data.json"
    
    with open(json_file_path) as json_file:
        database_mock = json.load(json_file)

    return database_mock

def get_tables_mocked_database():
    json_file_path = r'M:\projects\Python\PremierLeague\tests\mocks_data\mock_tables_data.json'
    
    with open(json_file_path) as json_file:
        database_mock = json.load(json_file)

    return database_mock

def get_players_mocked_database():
    json_file_path = r'M:\projects\Python\PremierLeague\tests\mocks_data\mock_players_data.json'
    
    with open(json_file_path) as json_file:
        database_mock = json.load(json_file)

    return database_mock

def test_program_window_preparation(mocker):

    def mock_section(section_name):
        
        def method(*args, **kwargs):
            nonlocal section_name
            
            master = args[0]

            # section_mock_object = MagicMock()

            # section_mock_object.widget = ttk.Frame(master)

            # section_label = tkinter.Label(section_mock_object.widget, text=section_name)
            # section_label.pack(pady=10)

            # return section_mock_object

            if section_name == 'matches_section':
                section = test_matches_section_view(container=master)
            elif section_name == 'tables_section':
                section = test_tables_section_view(container=master)
            elif section_name == 'teams_section':
                section = test_teams_section_view(container=master)
            elif section_name == 'players_section':
                section = test_players_section_view(container=master)

            return section

        return method

    mocker.patch("view.program_view.MatchesSection", side_effect=mock_section('matches_section'))
    mocker.patch("view.program_view.TablesSection", side_effect=mock_section('tables_section'))
    mocker.patch("view.program_view.TeamsSection", side_effect=mock_section('teams_section'))
    mocker.patch("view.program_view.PlayersSection", side_effect=mock_section('players_section'))

    mock_callback = MagicMock()
    mock_callback.get_matches_section_callback.return_value = None
    mock_callback.get_tables_section_callback.return_value = None
    mock_callback.get_teams_section_callback.return_value = None
    mock_callback.get_players_section_callback.return_value = None

    program_window = program_view.ProgramWindow(mock_callback)
    program_window.display()

def test_matches_section_view(container=None):
    if not container:
        container = tkinter.Tk()
        container.geometry('400x500')

    # container.pack(fill='both', expand=True)
    # container = tkinter.Frame(container)

    matches_mocked_database = get_matches_mocked_database()
    teams_mocked_database = get_teams_mocked_database()
    team_names = {record['id'] : record['team_name'] for record in teams_mocked_database}
    team_logos = dict()
    
    def resize_image_with_width(image, width):
        image_width, image_height = image.size
        image_ratio = image_width / image_height
        new_image_width = width
        new_image_height = int(new_image_width / image_ratio)

        image = image.resize((new_image_width, new_image_height))
        return image

    def prepare_team_logos(width):
        nonlocal teams_mocked_database, team_logos
        for record in teams_mocked_database:
            image_data = io.BytesIO(binascii.unhexlify(record['logo']))
            image = Image.open(image_data)
            image = resize_image_with_width(image, width)
            image = ImageTk.PhotoImage(image)
            team_logos[record['team_name']] = image

    def mock_get_week_data(*args, logos_width=35, **kwargs):
        prepare_team_logos(width=logos_width)
        nonlocal matches_mocked_database, team_names, team_logos
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

    section = matches_section.MatchesSection(container, mock_callback)
    if not container:
        section.widget.pack(fill='both', expand=True)

        container.mainloop()
    else:
        return section

def test_tables_section_view(container):
    if not container:
        container = tkinter.Tk()
        container.resizable(False, True)
        # container.geometry('600x600')

    def resize_image_with_width(image, width):
        image_width, image_height = image.size
        image_ratio = image_width / image_height
        new_image_width = width
        new_image_height = int(new_image_width / image_ratio)

        image = image.resize((new_image_width, new_image_height))
        return image

    def prepare_image(image_data, width):
        image = Image.open(io.BytesIO(binascii.unhexlify(image_data)))
        image = resize_image_with_width(image, width)
        image = ImageTk.PhotoImage(image)
        return image

    def mock_get_tables_data(logos_width=25, *args, **kwargs):
        tables_mocked_database = get_tables_mocked_database()
        teams_mocked_database = get_teams_mocked_database()

        team_logos = {record['id']:record['logo'] for record in teams_mocked_database}
        for record in tables_mocked_database:
            team_logo_data = team_logos[record['team_id']]
            record['team_logo'] = prepare_image(team_logo_data, logos_width)
        
        tables_mocked_database.sort(key=lambda record: record['points'])
        return tables_mocked_database

    mock_tables_callback = MagicMock()
    mock_tables_callback.get_tables_data = mock_get_tables_data

    section = tables_section.TablesSection(container=container, callback=mock_tables_callback)
    if not container:
        section.widget.pack(fill='both', expand=True)

        container.mainloop()
    else:
        return section


def test_teams_section_view(container=None):
    if not container:
        container = tkinter.Tk()
    # root.geometry("500x500")

    def resize_image_with_width(image, width):
        image_width, image_height = image.size
        image_ratio = image_width / image_height
        new_image_width = width
        new_image_height = int(new_image_width / image_ratio)

        image = image.resize((new_image_width, new_image_height))
        return image

    def prepare_image(image_data, width):
        image = Image.open(io.BytesIO(binascii.unhexlify(image_data)))
        image = resize_image_with_width(image, width)
        image = ImageTk.PhotoImage(image)
        return image
    
    def mock_get_teams_data(logos_width):
        teams_mocked_database = get_teams_mocked_database()
        for record in teams_mocked_database:
            record['logo'] = prepare_image(image_data=record['logo'], width=logos_width)

        return teams_mocked_database
    
    def mock_open_webbrowser_closure(url):
        def func():
            nonlocal url
            webbrowser.open(url)

        return func

    mock_teams_section_callback = MagicMock()
    mock_teams_section_callback.get_teams_data = mock_get_teams_data
    mock_teams_section_callback.open_webbrowser_closure = mock_open_webbrowser_closure

    section = teams_section.TeamsSection(container=container, callback=mock_teams_section_callback)
    if not container:
        section.widget.pack(fill='both', expand=True)

        container.mainloop()
    else:
        return section
    

def test_players_section_view(container=None):
    if not container:        
        container = tkinter.Tk()
    
    players_mocked_database = get_players_mocked_database()
    teams_mocked_database = get_teams_mocked_database()


    def resize_image_with_width(image, width):
        image_width, image_height = image.size
        image_ratio = image_width / image_height
        new_image_width = width
        new_image_height = int(new_image_width / image_ratio)

        image = image.resize((new_image_width, new_image_height))
        return image

    def prepare_image(image_data, width):
        image = Image.open(io.BytesIO(binascii.unhexlify(image_data)))
        image = resize_image_with_width(image, width)
        image = ImageTk.PhotoImage(image)
        return image
    
    def mock_get_players_data(team_name, player_picture_width):
        nonlocal players_mocked_database, teams_mocked_database

        team_names = {record['id'] : record['team_name'] for record in teams_mocked_database}
        
        team_players = list(filter(lambda record: team_names[record['team']] == team_name, players_mocked_database))

        sorted_dict = dict()

        for player in team_players:
            player['player_picture'] = prepare_image(player['player_picture'], width=player_picture_width)
            
            if player['position'] not in sorted_dict.keys():
                sorted_dict[player['position']] = list()
                
            sorted_dict[player['position']].append(player)
        
        return sorted_dict
    
    def mock_get_teams_list(logos_width):
        nonlocal teams_mocked_database

        teams_list = [{"team_name":record["team_name"], "team_logo":prepare_image(record["logo"], logos_width)} for record in teams_mocked_database]
        return teams_list
    
    mock_players_callback = MagicMock()
    mock_players_callback.get_players_data = mock_get_players_data
    mock_players_callback.get_teams_list = mock_get_teams_list

    section = players_section.PlayersSection(container=container, callback=mock_players_callback)
    if not container:
        section.widget.pack(fill='both', expand=True)

        container.mainloop()
    else:
        return section


