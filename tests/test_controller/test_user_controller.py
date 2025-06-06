import pytest, os, json, datetime, math
from controller.user_controller import MatchesSectionController, TeamsSectionController, TablesSectionController, PlayersSectionController
from unittest.mock import MagicMock, patch

# ======== Test MatchesSectionController class ========

@patch("model.model_factory.ModelFactory.create_model")
def test_matches_section_controller_initialization(mock_model_creator):
    mock_matches_model = MagicMock()
    mock_teams_model = MagicMock()

    def model_creator_side_effect(table_name):
        nonlocal mock_matches_model, mock_matches_model
        if table_name == 'matches':
            return mock_matches_model
        elif table_name == 'teams':
            return mock_teams_model
        else:
            pytest.fail(f'unexpected arguments to create_model method of ModelFactory class => table_name: {table_name}')

    mock_model_creator.side_effect = model_creator_side_effect

    controller = MatchesSectionController()

    mock_model_creator.assert_any_call(table_name='matches')
    mock_model_creator.assert_any_call(table_name='teams')

    assert controller.matches_database_controller == mock_matches_model
    assert controller.teams_database_controller == mock_teams_model

@patch("model.model_factory.ModelFactory.create_model")
def test_get_weeks_count_working_properly(mock_model_creator):
    mock_teams_database_controller = MagicMock()
    mock_teams_database_controller.get_records_count.return_value = 10
        
    mock_model_creator.return_value = mock_teams_database_controller

    controller = MatchesSectionController()
    weeks_count = controller.get_weeks_count()

    assert weeks_count == 18

@patch('controller.user_controller.WeekDataFormatter.format_data')
@patch('controller.user_controller.ImageManager.create_image_object')
@patch('model.model_factory.ModelFactory.create_model')
def test_get_week_data(mock_create_model, mock_create_image_object, mock_format_data):
    # Setup mock return values for logos, team names, and weekly match records
    fake_team_logos = {'Team A': 'hexdataA', 'Team B': 'hexdataB'}
    fake_team_names = {'1': 'Team A', '2': 'Team B'}
    fake_week_records = [{'match_id': 1, 'week': 5}, {'match_id': 2, 'week': 5}]
    formatted_data = "formatted week data"

    # Create mock controllers for teams and matches
    mock_matches_database_controller = MagicMock()
    mock_teams_database_controller = MagicMock()

    def model_creator_side_effect(table_name):
        if table_name == 'matches':
            return mock_matches_database_controller
        elif table_name == 'teams':
            return mock_teams_database_controller
        else:
            pytest.fail(f'unexpected arguments to create_model method of ModelFactory class => table_name: {table_name}')

    # Simulate the sequence of create_model calls:
    # First call returns teams controller, second call returns matches controller
    mock_create_model.side_effect = model_creator_side_effect

    # Define behavior for get_specific_column depending on input arguments
    def mock_get_specific_column(column, key):
        if column == 'name' and key == 'id':
            return fake_team_names  # Called during _get_team_names
        elif column == 'logo' and key == 'name':
            return fake_team_logos  # Called during _prepare_team_logos
        else:
            # Fail if unexpected arguments are passed
            pytest.fail(f'unexpected arguments to get_specific_column method of teams model : column: {column}, key: {key}') 

    # Assign side effect to simulate data retrieval for names and logos
    mock_teams_database_controller.get_specific_column.side_effect = mock_get_specific_column

    # Mock logo image creation
    mock_create_image_object.side_effect = lambda logo_data, width: f"Image({logo_data}, width={width})"

    # Mock the match data for the specified week
    mock_matches_database_controller.get_records.return_value = fake_week_records

    # Mock the output of the formatter
    mock_format_data.return_value = formatted_data

    # Instantiate controller and invoke get_week_data
    controller = MatchesSectionController()
    result = controller.get_week_data(week_number=5, logos_width=50)

    # Verify match data was fetched with correct week number
    mock_matches_database_controller.get_records.assert_called_once_with(week=5)

    # Verify image creation was attempted for each logo
    mock_create_image_object.assert_any_call('hexdataA', 50)
    mock_create_image_object.assert_any_call('hexdataB', 50)

    # Verify the format_data method was called with correct arguments
    mock_format_data.assert_called_once_with(
        fake_week_records,
        fake_team_names,
        {'Team A': 'Image(hexdataA, width=50)', 'Team B': 'Image(hexdataB, width=50)'}
    )

    # Assert the final result matches the expected formatted data
    assert result == formatted_data

@patch('model.model_factory.ModelFactory.create_model')
def test_get_this_week_number(mock_model_creator):
    mock_matches_database_model = MagicMock()

    def mock_model_factory(table_name):
        if table_name == 'matches':
            return mock_matches_database_model
        else:
            return None

    mock_model_creator.side_effect = mock_model_factory
    matches_section_controller = MatchesSectionController()

    mock_timestamps = {1: 1000, 2: 2000}
    mock_nearest_id = 2
    mock_week_number = 5

    # Mock methods
    matches_section_controller._find_nearest_id = MagicMock(return_value=mock_nearest_id)
    matches_section_controller.matches_database_controller.get_specific_column.return_value = mock_timestamps
    matches_section_controller.matches_database_controller.get_records.return_value = {
        "id": mock_nearest_id, "week_number": mock_week_number
    }

    result = matches_section_controller.get_this_week_number()

    # Assertions
    matches_section_controller.matches_database_controller.get_specific_column.assert_called_once_with('timestamp', 'id')
    matches_section_controller._find_nearest_id.assert_called_once_with(mock_timestamps)
    matches_section_controller.matches_database_controller.get_records.assert_called_once_with(id=mock_nearest_id)

    assert result == mock_week_number


@patch("controller.user_controller.datetime")
def test_find_nearest_id(mock_datetime):
    now = datetime.datetime(2025, 1, 1, 12, 0, 0)
    mock_datetime.datetime.now.return_value = now
  
    future_time_1 = int((now - datetime.timedelta(days=1)).timestamp())
    future_time_2 = int((now - datetime.timedelta(hours=1)).timestamp())
    future_time_3 = int((now - datetime.timedelta(days=2)).timestamp())
    future_time_4 = int((now + datetime.timedelta(days=1)).timestamp())
    future_time_5 = int((now + datetime.timedelta(hours=1)).timestamp())
    future_time_6 = int((now + datetime.timedelta(days=2)).timestamp())

    timestamps = {
        1: future_time_1,
        2: future_time_2,  
        3: future_time_3,
        4: future_time_4,  
        5: future_time_5,   # This is the closest
        6: future_time_6
    }
    with patch('model.model_factory.ModelFactory.create_model', return_value=None):
        controller = MatchesSectionController()
        result = controller._find_nearest_id(timestamps)

    assert result == 5

# ======== Test TablesSectionController class ========

# Test __init__ method initializes correct state
@patch('model.model_factory.ModelFactory.create_model')
def test_tables_section_controller_initialization(mock_create_model):
    mock_tables_database_controller = MagicMock()
    mock_teams_database_controller = MagicMock()

    def model_creator_side_effect(table_name):
        if table_name == 'tables':
            return mock_tables_database_controller
        elif table_name == 'teams':
            return mock_teams_database_controller
        else:
            pytest.fail(f'unexpected arguments to create_model method of ModelFactory class => table_name: {table_name}')

    mock_create_model.side_effect = model_creator_side_effect

    controller = TablesSectionController()

    assert controller.tables_database_controller == mock_tables_database_controller
    assert controller.teams_database_controller == mock_teams_database_controller
    assert mock_create_model.call_count == 2
    mock_create_model.assert_any_call(table_name='tables')
    mock_create_model.assert_any_call(table_name='teams')

# Test get_tables_data method behavior
@patch('controller.user_controller.TablesDataFormatter.format_data')
@patch('controller.user_controller.ImageManager.create_image_object')
@patch('model.model_factory.ModelFactory.create_model')
def test_get_tables_data(mock_create_model, mock_create_image_object, mock_format_data):
    # Setup test data
    fake_team_names = {'1': 'Team A', '2': 'Team B'}
    fake_logos = {'Team A': 'logoA_hex', 'Team B': 'logoB_hex'}
    fake_tables_data = {'Team A': {'points': 20}, 'Team B': {'points': 18}}
    formatted_data = {'some': 'formatted output'}

    # Create mock database controllers
    mock_teams_database_controller = MagicMock()
    mock_tables_database_controller = MagicMock()

    def model_creator_side_effect(table_name):
        if table_name == 'tables':
            return mock_tables_database_controller
        elif table_name == 'teams':
            return mock_teams_database_controller
        else:
            pytest.fail(f'unexpected arguments to create_model method of ModelFactory class => table_name: {table_name}')

    # First create_model call returns tables, second returns teams
    mock_create_model.side_effect = model_creator_side_effect

    # Mock get_specific_column behavior based on column + key
    def mock_get_specific_column(column, key):
        if column == 'team_name' and key == 'id':
            return fake_team_names
        elif column == 'logo' and key == 'team_name':
            return fake_logos
        else:
            pytest.fail(f"Unexpected arguments to get_specific_column: column={column}, key={key}")

    mock_teams_database_controller.get_specific_column.side_effect = mock_get_specific_column

    # Mock logo image creation
    mock_create_image_object.side_effect = lambda logo_data, width: f"Image({logo_data}, width={width})"

    # Mock tables data fetch
    mock_tables_database_controller.get_records.return_value = fake_tables_data

    # Mock formatted output
    mock_format_data.return_value = formatted_data

    # Create controller instance
    controller = TablesSectionController()

    # Call method under test
    result = controller.get_tables_data(logos_width=40)

    # Assertions
    mock_tables_database_controller.get_records.assert_called_once()
    mock_create_image_object.assert_any_call('logoA_hex', 40)
    mock_create_image_object.assert_any_call('logoB_hex', 40)
    mock_format_data.assert_called_once_with(
        fake_tables_data,
        fake_team_names,
        {'Team A': 'Image(logoA_hex, width=40)', 'Team B': 'Image(logoB_hex, width=40)'}
    )
    assert result == formatted_data

# ======== Test TeamsSectionController class ========

# Unit test for get_teams_data method
@patch('controller.user_controller.TeamsDataFormatter.format_data')
@patch('model.model_factory.ModelFactory.create_model')
def test_get_teams_data(mock_create_model, mock_format_data):
    # Setup test data
    fake_team_data = [
        {'id': 1, 'name': 'Team A', 'logo': 'logoA_hex'},
        {'id': 2, 'name': 'Team B', 'logo': 'logoB_hex'}
    ]
    formatted_data = {'some': 'formatted output'}

    # Create mock teams controller
    mock_teams_controller = MagicMock()
    mock_teams_controller.get_records.return_value = fake_team_data

    # create_model should return the teams controller
    mock_create_model.return_value = mock_teams_controller

    # Mock format_data return
    mock_format_data.return_value = formatted_data

    # Create controller and call method
    controller = TeamsSectionController()
    result = controller.get_teams_data(logos_width=40)

    # Assertions
    mock_teams_controller.get_records.assert_called_once()
    mock_format_data.assert_called_once_with(fake_team_data, 40)
    assert result == formatted_data


# Unit test to check correct initialization of TeamsSectionController
@patch('model.model_factory.ModelFactory.create_model')
def test_teams_section_controller_initialization(mock_create_model):
    # Setup
    mock_teams_controller = MagicMock()
    mock_create_model.return_value = mock_teams_controller

    # Create controller
    controller = TeamsSectionController()

    # Assert correct initialization
    assert controller.teams_database_controller == mock_teams_controller
    mock_create_model.assert_called_once_with(table_name='teams')


# ======== Test PlayersSectionController class ========

# Test for initializer to confirm correct state setup
@patch('model.model_factory.ModelFactory.create_model')
def test_players_section_controller_init(mock_create_model):
    mock_players_database_controller = MagicMock()
    mock_teams_database_controller = MagicMock()

    def model_creator_side_effect(table_name):
        if table_name == 'players':
            return mock_players_database_controller
        elif table_name == 'teams':
            return mock_teams_database_controller
        else:
            pytest.fail(f'unexpected arguments to create_model method of ModelFactory class => table_name: {table_name}')

    # First call returns players controller, second returns teams controller
    mock_create_model.side_effect = model_creator_side_effect

    controller = PlayersSectionController()

    assert controller.player_database_controller == mock_players_database_controller
    assert controller.teams_database_controller == mock_teams_database_controller


# Test get_players_data behavior
@patch('controller.user_controller.TeamsDataFormatter.format_data')
@patch('model.model_factory.ModelFactory.create_model')
def test_get_players_data(mock_create_model, mock_format_data):
    mock_players_database_controller = MagicMock()
    mock_teams_database_controller = MagicMock()

    def model_creator_side_effect(table_name):
        if table_name == 'players':
            return mock_players_database_controller
        elif table_name == 'teams':
            return mock_teams_database_controller
        else:
            pytest.fail(f'unexpected arguments to create_model method of ModelFactory class => table_name: {table_name}')

    mock_create_model.side_effect = model_creator_side_effect

    fake_team_name = "Team A"
    fake_picture_width = 40
    fake_team_players = [{'player': 'Player 1'}, {'player': 'Player 2'}]
    formatted_data = [{'player': 'Formatted Player 1'}, {'player': 'Formatted Player 2'}]

    mock_teams_database_controller.get_records.return_value = fake_team_players
    mock_format_data.return_value = formatted_data

    controller = PlayersSectionController()
    result = controller.get_players_data(team_name=fake_team_name, picture_width=fake_picture_width)

    mock_teams_database_controller.get_records.assert_called_once_with(team_name=fake_team_name)
    mock_format_data.assert_called_once_with(fake_team_players, fake_picture_width)
    assert result == formatted_data


# Test get_teams_data behavior
@patch('model.model_factory.ModelFactory.create_model')
def test_get_teams_data(mock_create_model):
    mock_players_database_controller = MagicMock()
    mock_teams_database_controller = MagicMock()

    def model_creator_side_effect(table_name):
        if table_name == 'players':
            return mock_players_database_controller
        elif table_name == 'teams':
            return mock_teams_database_controller
        else:
            pytest.fail(f'unexpected arguments to create_model method of ModelFactory class => table_name: {table_name}')


    mock_create_model.side_effect = model_creator_side_effect

    fake_logos = {
        'Team A': 'LogoA',
        'Team B': 'LogoB'
    }
    mock_teams_database_controller.get_specific_column.return_value = fake_logos

    controller = PlayersSectionController()
    result = controller.get_teams_data(logos_width=35)

    expected = [
        {'team_name': 'Team A', 'team_logo': 'LogoA'},
        {'team_name': 'Team B', 'team_logo': 'LogoB'}
    ]

    assert result == expected
