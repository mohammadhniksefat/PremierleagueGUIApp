import pytest
from premierleague.model.database_manager import SQliteDatabaseManager
from unittest.mock import patch, MagicMock

def test_configure_model_sets_up_model_and_registers_cleanup():
    manager = SQliteDatabaseManager()
    model = MagicMock()
    model.database_address = ":memory:"

    with patch("sqlite3.connect") as mock_connect, \
         patch("atexit.register") as mock_atexit, \
         patch("premierleague.model.database_manager.DatabaseManager.__init__") as mock_super_init:

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        manager.configure_model(model)

        mock_super_init.assert_called_once()
        mock_connect.assert_called_once_with(":memory:")
        assert manager._connection == mock_connection
        assert model.connection == mock_connection
        assert model.cursor == mock_cursor
        mock_atexit.assert_called_once_with(manager.clean_up)

def test_clean_up_closes_connection():
    manager = SQliteDatabaseManager()
    mock_connection = MagicMock()
    manager._connection = mock_connection

    manager.clean_up()

    mock_connection.close.assert_called_once()  
