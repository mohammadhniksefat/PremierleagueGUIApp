import pytest, os, json, datetime, math
from controller import user_controller
from model import database_controller
from unittest.mock import MagicMock 

def is_called_with_kw_argument(calls, key, value):
    for call in calls:
        kwargs = call.kwargs
        if key in kwargs.keys() and kwargs[key] == value:
            return True
        else:
            return False

def test_main_controller_functionality():
    controller = user_controller.MainController()

    assert isinstance(controller.get_matches_section_callback(), user_controller.MatchesSectionController)
    assert isinstance(controller.get_teams_section_callback(), user_controller.TeamsSectionController)
    assert isinstance(controller.get_tables_section_callback(), user_controller.TablesSectionController)

def test_matches_section_controller(mocker):
    matches_section_controller = user_controller.MatchesSectionController()

    mock_team_names = MagicMock()
    mock_team_logos = MagicMock()

    def func(column, sort_by):
        nonlocal mock_team_names, mock_team_logos

        if column == 'name':
            return mock_team_names
        elif column == 'logo':
            return mock_team_logos
        else:
            raise ValueError('unexpected arguments!')

    mocker.patch('model.models.base_model.BaseModel.get_specific_column', side_effect=func)

    mock_data = MagicMock()

    mock_get_week_records = mocker.patch('model.models.base_model.BaseModel.get_records', return_value=mock_data)

    mock_formatted_data = MagicMock()
    mock_data_formatter = mocker.patch('controller.user_controller.WeekDataFormatter.format_data', return_value=mock_formatted_data)

    returned_value = matches_section_controller.get_week_data(week_number=10)
    mock_get_week_records.assert_called_once_with(week=10)

    mock_data_formatter.assert_any_call(mock_data, mock_team_names, mock_team_logos)

    assert returned_value == mock_formatted_data

    ##################
    
    mock_weeks_count = MagicMock()
    mock_get_weeks_count = mocker.patch('model.models.base_model.BaseModel.get_records_count', return_value=mock_weeks_count)

    returned_value = matches_section_controller.get_weeks_count()
    mock_get_weeks_count.assert_called_once()
    assert returned_value == mock_weeks_count

    mock_this_week_number = MagicMock()
    mock_get_records_within_period = mocker.patch(
        'model.models.base_model.BaseModel.get_records_within_period', 
        return_value=[{'week_number':mock_this_week_number}]
    )
    
    returned_value = matches_section_controller.get_this_week_number()

    assert is_called_with_kw_argument(calls=mock_get_records_within_period.call_args_list, key='period', value='week')
    # mock_get_records_within_period.assert_any_call(period='week')
    assert returned_value == mock_this_week_number