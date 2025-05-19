import pytest
import os
from sqlite3 import DatabaseError
from unittest.mock import patch, MagicMock
from model.model_factory import ModelFactory, DatabaseTypeChecker
from pathlib import Path

# ---------------------------
# Tests for ModelFactory
# ---------------------------

@pytest.mark.parametrize("table_name, model_class_path", [
    ("players", "model.models.sqlite_models.PlayersModel"),
    ("teams", "model.models.sqlite_models.TeamsModel"),
    ("matches", "model.models.sqlite_models.MatchesModel"),
    ("tables", "model.models.sqlite_models.TablesModel"),
])
def test_create_model_valid_tables(table_name, model_class_path):
    with patch("model.model_factory.DatabaseTypeChecker.check_sqlite_db", return_value=True), \
         patch(model_class_path) as mock_model:
        model = ModelFactory.create_model(table_name, "fake_path")
        mock_model.assert_called_once_with("fake_path")
        assert model == mock_model.return_value

def test_create_model_with_default_path():
    with patch("model.model_factory.DatabaseTypeChecker.check_sqlite_db", return_value=True), \
         patch("model.models.sqlite_models.PlayersModel") as mock_model, \
         patch("model.model_factory.ModelFactory._get_default_db_address", return_value="resolved_path"):
        model = ModelFactory.create_model("players")
        mock_model.assert_called_once_with("resolved_path")
        assert model == mock_model.return_value

def test_create_model_with_custom_path():
    with patch("model.model_factory.DatabaseTypeChecker.check_sqlite_db", return_value=True), \
         patch("model.models.sqlite_models.PlayersModel") as mock_model:
        model = ModelFactory.create_model("players", db_address="custom_db_address")
        mock_model.assert_called_once_with("custom_db_address")
        assert model == mock_model.return_value

def test_create_model_invalid_table():
    with patch("model.model_factory.DatabaseTypeChecker.check_sqlite_db", return_value=True):
        with pytest.raises(ValueError, match="Unknown table name!"):
            ModelFactory.create_model("invalid_table", "fake_path")

def test_create_model_invalid_database():
    with patch("model.model_factory.DatabaseTypeChecker.check_sqlite_db", return_value=False):
        with pytest.raises(ValueError, match="invalid database type!"):
            ModelFactory.create_model("players", "fake_path")

def test_get_default_db_address_resolves_path():
    default_path = ModelFactory._get_default_db_address()
    expected_path = str(Path(__file__).parent / "../" / "data" / "main_database.db")
    assert default_path == expected_path

def test_get_default_db_address_exists():
    path = ModelFactory._get_default_db_address()
    assert os.path.exists(path), f"Default DB path does not exist: {path}"

# ---------------------------
# Tests for DatabaseTypeChecker
# ---------------------------

def test_check_sqlite_db_success():
    with patch("sqlite3.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        result = DatabaseTypeChecker.check_sqlite_db("some_path")
        mock_connect.assert_called_once_with("some_path")
        mock_conn.close.assert_called_once()
        assert result is True

def test_check_sqlite_db_failure():
    with patch("sqlite3.connect", side_effect=DatabaseError):
        result = DatabaseTypeChecker.check_sqlite_db("bad_path")
        assert result is False