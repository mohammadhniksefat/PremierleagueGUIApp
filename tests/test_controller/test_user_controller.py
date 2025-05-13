import pytest, os, json, datetime, math
from controller.user_controller import MatchesSectionController
from unittest.mock import MagicMock, patch


@patch("model.model_factory.ModelFactory.create_model")
def test_matches_section_controller_initialization(mock_model_creator):
    mock_matches_model = MagicMock()
    mock_teams_model = MagicMock()

    def side_effect(model):
        nonlocal mock_matches_model, mock_matches_model
        if model == 'matches':
            return mock_matches_model
        elif model == 'teams':
            return mock_teams_model
        else:
            pytest.fail("shouldn't pass anything except 'matches' or 'teams' to model creator function")

    mock_model_creator.side_effect = side_effect

    controller = MatchesSectionController()

    mock_model_creator.assert_any_call(model='matches')
    mock_model_creator.assert_any_call(model='teams')

    assert controller.matches_database_controller == mock_matches_model
    assert controller.teams_database_controller == mock_teams_model

@patch("model.model_factory.ModelFactory.create_model")
def test_get_weeks_count_working_properly(mock_model_creator):
    mock_teams_database_controller = MagicMock()
    mock_teams_database_controller.get_records_count.return_value = 10

    def side_effect(model):
        nonlocal mock_teams_database_controller
        if model == 'matches':
            return MagicMock()
        elif model == 'teams':
            return mock_teams_database_controller
        else:
            pytest.fail("shouldn't pass anything except 'matches' or 'teams' to model creator function")
        
    mock_model_creator.side_effect = side_effect

    controller = MatchesSectionController()
    weeks_count = controller.get_weeks_count()

    # mock_teams_database_controller.get_records_count.assert_called_once()

    assert weeks_count == 18

@patch('model.model_factory.ModelFactory.create_model')
def test_get_this_week_number(mock_create_model):
    mock_matches_database_controller = MagicMock()
    mock_matches_database_controller.get_records_within_period.return_value = [{'week_number': 14}]
    def side_effect(model):
        if model == 'matches':
            return mock_matches_database_controller
        elif model == 'teams':
            return MagicMock()
        else:
            pytest.fail("shouldn't pass anything except 'matches' or 'teams' to model creator function")

    mock_create_model.side_effect = side_effect

    controller = MatchesSectionController()
    week = controller.get_this_week_number()

    assert week == 14
    mock_matches_database_controller.get_records_within_period.assert_called_once()
    args, kwargs = mock_matches_database_controller.get_records_within_period.call_args
    assert kwargs['period'] == 'week'
    assert isinstance(kwargs['timestamp'], datetime.datetime)


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
    mock_teams_controller = MagicMock()
    mock_matches_controller = MagicMock()

    # Simulate the sequence of create_model calls:
    # First call returns teams controller, second call returns matches controller
    mock_create_model.side_effect = [mock_teams_controller, mock_matches_controller]

    # Define behavior for get_specific_column depending on input arguments
    def mock_get_specific_column(column, sort_by):
        if column == 'name' and sort_by == 'id':
            return fake_team_names  # Called during _get_team_names
        elif column == 'logo' and sort_by == 'name':
            return fake_team_logos  # Called during _prepare_team_logos
        else:
            # Fail if unexpected arguments are passed
            pytest.fail(f'unexpected arguments to get_specific_column method of teams model : column: {column}, sort_by: {sort_by}') 

    # Assign side effect to simulate data retrieval for names and logos
    mock_teams_controller.get_specific_column.side_effect = mock_get_specific_column

    # Mock logo image creation
    mock_create_image_object.side_effect = lambda logo_data, width: f"Image({logo_data}, width={width})"

    # Mock the match data for the specified week
    mock_matches_controller.get_records.return_value = fake_week_records

    # Mock the output of the formatter
    mock_format_data.return_value = formatted_data

    # Instantiate controller and invoke get_week_data
    controller = MatchesSectionController()
    result = controller.get_week_data(week_number=5, logos_width=50)

    # Verify match data was fetched with correct week number
    mock_matches_controller.get_records.assert_called_once_with(week=5)

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

