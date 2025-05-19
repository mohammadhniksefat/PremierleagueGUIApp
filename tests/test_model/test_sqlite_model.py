import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from model.models.sqlite_models import SQliteModel, TeamsModel, MatchesModel, PlayersModel, TablesModel

@pytest.fixture
def db_model():
    with patch('model.database_manage.SQliteDatabaseManager') as mock_db_manager_class, \
         patch.object(SQliteModel, 'get_column_names', return_value=["id", "email", "username", "full_name", "age"]), \
         patch.object(SQliteModel, 'get_unique_constraint', return_value=["email", "username"]), \
         patch.object(SQliteModel, 'get_required_column_names', return_value=["email", "username"]):

        # Mock the configure_model method
        def configure_model(model):
            model.connection = sqlite3.connect(":memory:")
            model.cursor = model.connection.cursor()

        mock_db_manager = MagicMock()
        mock_db_manager.configure_model.side_effect = configure_model
        mock_db_manager_class.return_value = mock_db_manager

        model = SQliteModel(database_address=None, table_name="users")

        model.cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL,
                username TEXT NOT NULL,
                full_name TEXT,
                age INTEGER,
                UNIQUE(email, username)
            )
        """)
        model.connection.commit()

        yield model

        model.connection.close()

@pytest.fixture
def setup_an_empty_model():
    with patch('model.database_manager.SQliteDatabaseManager') as mock_manager_class:
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        model = SQliteModel(database_address=None, table_name='test_table')
        model.connection = sqlite3.connect(":memory:")
        model.cursor = model.connection.cursor()

        yield model
        model.connection.close()

@pytest.fixture
def mock_initialization_test_dependencies():
    with patch("model.models.sqlite_model.SQliteDatabaseManager") as MockDBManager, \
         patch.object(SQliteModel, "get_column_names", return_value={"id", "email", "username", "age"}) as mock_colnames, \
         patch.object(SQliteModel, "get_unique_constraint", return_value=["email", "username"]) as mock_unique, \
         patch.object(SQliteModel, "get_required_column_names", return_value={"email", "username"}) as mock_required:

        db_manager_instance = MagicMock()
        MockDBManager.return_value = db_manager_instance

        # Provide a dummy configure_model to set dummy cursor and connection
        dummy_cursor = MagicMock()
        dummy_connection = MagicMock()
        
        def dummy_config(model):
            model.cursor = dummy_cursor
            model.connection = dummy_connection

        db_manager_instance.configure_model.side_effect = dummy_config

        yield {
            "MockDBManager": MockDBManager,
            "mock_colnames": mock_colnames,
            "mock_unique": mock_unique,
            "mock_required": mock_required,
            "dummy_cursor": dummy_cursor,
            "dummy_connection": dummy_connection,
            "db_manager_instance": db_manager_instance,
        }

def test_init_sets_attributes_correctly(mock_initialization_test_dependencies):
    mock_dependencies = mock_initialization_test_dependencies
    
    model = SQliteModel(database_address="fake.db", table_name="users")

    # Basic property checks
    assert model.database_address == "fake.db"
    assert model.table_name == "users"
    assert model.unique_constraint == ["email", "username"]
    assert model.column_names == {"id", "email", "username", "age"}
    assert model.required_columns == {"email", "username"}

    # Connection and cursor should be set by configure_model
    assert model.cursor == mock_dependencies["dummy_cursor"]
    assert model.connection == mock_dependencies["dummy_connection"]

    # Confirm configure_model was called
    mock_dependencies["db_manager_instance"].configure_model.assert_called_once_with(model)

def test_create_table_if_not_exist_executes_correct_schema(setup_an_empty_model):
    model = setup_an_empty_model
    fake_schema = "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY);"

    with patch.dict(SQliteModel.schemas, {'test_table': fake_schema}), \
         patch.object(model.cursor, 'execute', wraps=model.cursor.execute) as mock_execute:
        
        model.create_table_if_not_exist()

        mock_execute.assert_called_once_with(fake_schema)


# ============= Test get_records() method =============  

# Helper function to insert test data
def insert_sample_users_test_get_records(model: SQliteModel):
    sample_data = [
        (1, "alice@example.com", "alice", "Alice A.", 30),
        (2, "bob@example.com", "bob", "Bob B.", 25),
        (3, "charlie@example.com", "charlie", "Charlie C.", 30),
    ]
    model.cursor.executemany("""
        INSERT INTO users (id, email, username, full_name, age)
        VALUES (?, ?, ?, ?, ?)
    """, sample_data)
    model.connection.commit()

# --- TC1: No filters passed — should return all records
def test_get_records_no_filters_returns_all(db_model):
    insert_sample_users_test_get_records(db_model)
    records = db_model.get_records()
    assert len(records) == 3
    assert any(record[1] == "alice@example.com" for record in records)

# --- TC2: Valid filter on 'age'
def test_get_records_valid_filter(db_model):
    insert_sample_users_test_get_records(db_model)
    records = db_model.get_records(age=30)
    assert len(records) == 2
    assert all(record[4] == 30 for record in records)

# --- TC3: Mixed valid and invalid filters
def test_get_records_partial_valid_kwargs(db_model):
    insert_sample_users_test_get_records(db_model)
    records = db_model.get_records(age=25, non_existing="value")
    assert len(records) == 1
    assert records[0][2] == "bob"

# --- TC4: All filters invalid — should return all
def test_get_records_all_invalid_kwargs_returns_all(db_model):
    insert_sample_users_test_get_records(db_model)
    records = db_model.get_records(foo="bar", something=123)
    assert len(records) == 3

# --- TC5: No data in table — return empty list
def test_get_records_empty_table_returns_empty(db_model):
    records = db_model.get_records()
    assert records == []

# --- TC6: Valid filter, no matching data
def test_get_records_valid_filter_no_match_returns_empty(db_model):
    insert_sample_users_test_get_records(db_model)
    records = db_model.get_records(age=100)
    assert records == []


# =============== Test get_specific_column() method ===============
    
def insert_sample_users_test_get_specific_column(model: SQliteModel):
    sample_data = [
        (1, "alice@example.com", "alice", "Alice A.", 30),
        (2, "bob@example.com", "bob", "Bob B.", 25),
        (3, "charlie@example.com", "charlie", "Charlie C.", 35),
    ]
    model.cursor.executemany("""
        INSERT INTO users (id, email, username, full_name, age)
        VALUES (?, ?, ?, ?, ?)
    """, sample_data)
    model.connection.commit()

# --- TC1: Only column specified — returns list of values
def test_get_specific_column_as_list(db_model):
    insert_sample_users_test_get_specific_column(db_model)
    result = db_model.get_specific_column("username")
    assert result == ["alice", "bob", "charlie"]

# --- TC2: Column and key specified — returns dictionary
def test_get_specific_column_as_dict(db_model):
    insert_sample_users_test_get_specific_column(db_model)
    result = db_model.get_specific_column("age", key="username")
    assert result == {"alice": 30, "bob": 25, "charlie": 35}

# --- TC3: Invalid column name — raises ValueError
def test_get_specific_column_invalid_column(db_model):
    insert_sample_users_test_get_specific_column(db_model)
    with pytest.raises(ValueError, match="Invalid column:"):
        db_model.get_specific_column("nonexistent")

# --- TC4: Invalid key name — raises ValueError
def test_get_specific_column_invalid_key(db_model):
    insert_sample_users_test_get_specific_column(db_model)
    with pytest.raises(ValueError, match="Invalid key column:"):
        db_model.get_specific_column("age", key="nonexistent")

# --- TC5: No data in table — returns empty list or dict
def test_get_specific_column_empty_table_returns_empty(db_model):
    assert db_model.get_specific_column("username") == []
    assert db_model.get_specific_column("age", key="username") == {}

# ================= Test get_records_count() method =================
    
# Sample data helper
def insert_sample_users_test_get_records_count(model: SQliteModel):
    sample_data = [
        (1, "alice@example.com", "alice", "Alice A.", 30),
        (2, "bob@example.com", "bob", "Bob B.", 25),
    ]
    model.cursor.executemany("""
        INSERT INTO users (id, email, username, full_name, age)
        VALUES (?, ?, ?, ?, ?)
    """, sample_data)
    model.connection.commit()

# --- TC1: Empty table — should return 0
def test_get_records_count_empty_table(db_model):
    count = db_model.get_records_count()
    assert count == 0

# --- TC2: Table with multiple records — should return correct count
def test_get_records_count_with_data(db_model):
    insert_sample_users_test_get_records_count(db_model)
    count = db_model.get_records_count()
    assert count == 2

# --- TC3: Table with one record — should return 1
def test_get_records_count_one_record(db_model):
    db_model.cursor.execute("""
        INSERT INTO users (id, email, username, full_name, age)
        VALUES (?, ?, ?, ?, ?)
    """, (3, "charlie@example.com", "charlie", "Charlie C.", 40))
    db_model.connection.commit()
    count = db_model.get_records_count()
    assert count == 1


# --- TC1: Test get_column_names returns correct set of columns
def test_get_column_names_returns_correct_columns(db_model):
    expected_columns = {"id", "email", "username", "full_name", "age"}
    actual_columns = db_model.get_column_names()
    assert isinstance(actual_columns, set)
    assert actual_columns == expected_columns

# --- TC2: Test get_required_column_names returns NOT NULL columns
def test_get_required_column_names_returns_not_null_columns(db_model):
    required_columns = db_model.get_required_column_names()
    assert isinstance(required_columns, set)
    assert required_columns == {"email", "username"}

# --- TC3: Test get_table_unique_constraint returns correct unique columns
def test_get_table_unique_constraint_returns_unique_columns(db_model):
    unique_columns = db_model.get_table_unique_constraint()
    # The table has a UNIQUE constraint on (email, username)
    assert isinstance(unique_columns, list)
    assert set(unique_columns) == {"email", "username"}


# ================== Test create_records() method ==================
    
# --- TC1: Successful record creation with all required and optional fields
def test_create_record_successful_insertion(db_model):
    record = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "age": 28
    }
    db_model.create_record(record)

    db_model.cursor.execute("SELECT * FROM users WHERE email = ?", (record["email"],))
    result = db_model.cursor.fetchone()
    assert result is not None
    assert result[1] == "test@example.com"  # email
    assert result[2] == "testuser"          # username

# --- TC2: Missing required field (email)
def test_create_record_missing_required_field_raises(db_model):
    record = {
        "username": "noemailuser",
        "full_name": "No Email",
        "age": 22
    }
    with pytest.raises(ValueError, match="Missing required columns: email"):
        db_model.create_record(record)

# --- TC3: Empty dictionary provided
def test_create_record_empty_dict_raises(db_model):
    with pytest.raises(ValueError, match="Empty dictionary provided"):
        db_model.create_record({})

# --- TC4: Extra fields beyond valid columns are ignored
def test_create_record_ignores_extra_keys(db_model):
    record = {
        "email": "extra@example.com",
        "username": "extrauser",
        "full_name": "Extra User",
        "age": 33,
        "unrelated_column": "should be ignored"
    }
    db_model.create_record(record)

    db_model.cursor.execute("SELECT * FROM users WHERE email = ?", ("extra@example.com",))
    result = db_model.cursor.fetchone()
    assert result is not None
    assert result[1] == "extra@example.com"
    assert "unrelated_column" not in db_model.get_column_names()

# ================ Test get_records_count() method ================
    
# Helper to insert sample data
def insert_sample_users_test_is_record_exists(model):
    users = [
        (1, "alice@example.com", "alice", "Alice A.", 30),
        (2, "bob@example.com", "bob", "Bob B.", 25),
    ]
    model.cursor.executemany("""
        INSERT INTO users (id, email, username, full_name, age)
        VALUES (?, ?, ?, ?, ?)
    """, users)
    model.connection.commit()


# --- TC1: Record exists for valid filter
def test_is_record_exists_returns_true_if_record_found(db_model):
    insert_sample_users_test_is_record_exists(db_model)
    exists = db_model.is_record_exists(email="alice@example.com")
    assert exists is True


# --- TC2: No matching record
def test_is_record_exists_returns_false_if_no_match(db_model):
    insert_sample_users_test_is_record_exists(db_model)
    exists = db_model.is_record_exists(email="nonexistent@example.com")
    assert exists is False


# --- TC3: Record exists with multiple filters
def test_is_record_exists_with_multiple_valid_filters(db_model):
    insert_sample_users_test_is_record_exists(db_model)
    exists = db_model.is_record_exists(email="bob@example.com", username="bob")
    assert exists is True


# --- TC4: One correct, one incorrect filter — should return False
def test_is_record_exists_with_one_correct_and_one_wrong_filter_returns_false(db_model):
    insert_sample_users_test_is_record_exists(db_model)
    exists = db_model.is_record_exists(email="alice@example.com", username="bob")  # mismatched pair
    assert exists is False

# --- TC5: One valid, one invalid filter (ignored)
def test_is_record_exists_with_partial_invalid_filters(db_model):
    insert_sample_users_test_is_record_exists(db_model)
    exists = db_model.is_record_exists(email="alice@example.com", invalid_field="abc")
    assert exists is True


# --- TC6: All filters invalid (treated as no filters → returns all records → True)
def test_is_record_exists_with_all_invalid_filters(db_model):
    insert_sample_users_test_is_record_exists(db_model)
    exists = db_model.is_record_exists(foo="bar")
    assert exists is True  # get_records() returns all if all filters invalid

# ================== Test delete_records() ==================
    

def insert_sample_users_for_delete_test(model):
    users = [
        (1, "alice@example.com", "alice", "Alice A.", 30),
        (2, "bob@example.com", "bob", "Bob B.", 25),
        (3, "charlie@example.com", "charlie", "Charlie C.", 30),
        (4, "dana@example.com", "dana", "Dana D.", 40),
    ]
    model.cursor.executemany("""
        INSERT INTO users (id, email, username, full_name, age)
        VALUES (?, ?, ?, ?, ?)
    """, users)
    model.connection.commit()


# --- TC1: Deletes a matching record and returns it
def test_delete_single_matching_record(db_model):
    insert_sample_users_for_delete_test(db_model)
    deleted = db_model.delete_records(email="alice@example.com")
    
    assert isinstance(deleted, list)
    assert len(deleted) == 1
    assert deleted[0]["email"] == "alice@example.com"
    
    # Ensure it was actually deleted
    remaining = db_model.get_records()
    assert all(record["email"] != "alice@example.com" for record in remaining)


# --- TC2: No matching record returns empty list
def test_delete_no_matching_record_returns_empty(db_model):
    insert_sample_users_for_delete_test(db_model)
    deleted = db_model.delete_records(email="nonexistent@example.com")
    assert deleted == []


# --- TC3: Multiple filters - deletes only if all match
def test_delete_with_multiple_matching_filters(db_model):
    insert_sample_users_for_delete_test(db_model)
    deleted = db_model.delete_records(email="bob@example.com", username="bob")
    
    assert len(deleted) == 1
    assert deleted[0]["username"] == "bob"
    
    remaining = db_model.get_records()
    assert all(record["username"] != "bob" for record in remaining)


# --- TC4: Valid column, wrong value - nothing deleted
def test_delete_with_partial_filter_match_fails(db_model):
    insert_sample_users_for_delete_test(db_model)
    deleted = db_model.delete_records(email="alice@example.com", username="bob")
    assert deleted == []

    # Nothing should be deleted
    remaining = db_model.get_records()
    assert len(remaining) == 2


# --- TC5: Raises ValueError on no conditions
import pytest

def test_delete_raises_error_if_no_kwargs(db_model):
    insert_sample_users_for_delete_test(db_model)
    with pytest.raises(ValueError, match="No conditions provided"):
        db_model.delete_records()


# --- TC6: Raises ValueError on invalid column
def test_delete_raises_error_on_invalid_column(db_model):
    insert_sample_users_for_delete_test(db_model)
    with pytest.raises(ValueError, match="Invalid columns: foo"):
        db_model.delete_records(foo="bar")


# --- TC7: Deletes multiple records with common column value
def test_delete_multiple_records_with_common_value(db_model):
    insert_sample_users_for_delete_test(db_model)
    deleted = db_model.delete_records(age=30)

    assert isinstance(deleted, list)
    assert len(deleted) == 2
    emails_deleted = {record["email"] for record in deleted}
    assert "alice@example.com" in emails_deleted
    assert "charlie@example.com" in emails_deleted

    remaining = db_model.get_records()
    remaining_emails = {record["email"] for record in remaining}
    assert "alice@example.com" not in remaining_emails
    assert "charlie@example.com" not in remaining_emails


# ======================= Test update_record() method ======================
    
def insert_sample_users(db_model):
    sample_users = [
        ("alice", "alice@example.com", "Alice Smith", 30),
        ("bob", "bob@example.com", "Bob Johnson", 40),
        ("charlie", "charlie@example.com", "Charlie Lee", 25)
    ]

    for username, email, full_name, age in sample_users:
        db_model.cursor.execute(
            """
            INSERT INTO users (username, email, full_name, age)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, full_name, age)
        )

    db_model.connection.commit()

# --- TC1: Successfully updates a single field using a unique constraint
def test_update_single_field_success(db_model):
    insert_sample_users(db_model)

    db_model.update_record({
        "email": "alice@example.com",
        "username": "alice",
        "age": 35
    })

    updated = db_model.get_records(email="alice@example.com")[0]
    assert updated["age"] == 35
    assert updated["full_name"] == "Alice Smith"

# --- TC2: Successfully updates multiple fields
def test_update_multiple_fields_success(db_model):
    insert_sample_users(db_model)

    db_model.update_record({
        "email": "bob@example.com",
        "username": "bob",
        "age": 45,
        "full_name": "Robert Johnson"
    })

    updated = db_model.get_records(email="bob@example.com")[0]
    assert updated["age"] == 45
    assert updated["full_name"] == "Robert Johnson"

# --- TC3: Raises error if a unique constraint field is missing
def test_update_raises_if_unique_constraint_missing(db_model):
    insert_sample_users(db_model)

    with pytest.raises(ValueError, match="Missing unique constraint fields"):
        db_model.update_record({
            "email": "alice@example.com",
            "age": 35  # username is missing
        })

# --- TC4: Raises error if no matching record found
def test_update_raises_if_no_record_matches(db_model):
    insert_sample_users(db_model)

    with pytest.raises(ValueError, match="No matching record found"):
        db_model.update_record({
            "email": "nonexistent@example.com",
            "username": "ghost",
            "age": 50
        })

# --- TC5: Raises error if no updatable fields are provided
def test_update_raises_if_no_fields_to_update(db_model):
    insert_sample_users(db_model)

    with pytest.raises(ValueError, match="No fields to update after filtering"):
        db_model.update_record({
            "email": "alice@example.com",
            "username": "alice"
        })

# --- TC6: Ignores extra fields not in table
def test_update_ignores_invalid_fields(db_model):
    insert_sample_users(db_model)

    db_model.update_record({
        "email": "charlie@example.com",
        "username": "charlie",
        "age": 28,
        "non_existent_field": "foobar",
        "another_fake_field": 123
    })

    updated = db_model.get_records(email="charlie@example.com")[0]
    assert updated["age"] == 28
    assert "non_existent_field" not in updated
    assert "another_fake_field" not in updated

# ====================== Players Model specific Tests ======================

def test_players_model_initializer():
    mock_address = "dummy.db"

    with patch("model.players_model.SQliteModel.__init__") as mock_super_init, \
         patch.object(PlayersModel, "create_table_if_not_exist") as mock_create_table:

        mock_super_init.return_value = None
        instance = PlayersModel(mock_address)

        mock_super_init.assert_called_once_with(mock_address, "players")
        mock_create_table.assert_called_once()

# ====================== Teams Model specific Tests ======================

def test_teams_model_initializer():
    mock_address = "dummy.db"

    with patch("model.players_model.SQliteModel.__init__") as mock_super_init, \
         patch.object(TeamsModel, "create_table_if_not_exist") as mock_create_table:

        mock_super_init.return_value = None
        instance = TeamsModel(mock_address)

        mock_super_init.assert_called_once_with(mock_address, "teams")
        mock_create_table.assert_called_once()

# ====================== Matches Model specific Tests ======================

def test_matches_model_initializer():
    mock_address = "dummy.db"

    with patch("model.players_model.SQliteModel.__init__") as mock_super_init, \
         patch.object(MatchesModel, "create_table_if_not_exist") as mock_create_table:

        mock_super_init.return_value = None
        instance = MatchesModel(mock_address)

        mock_super_init.assert_called_once_with(mock_address, "matches")
        mock_create_table.assert_called_once()

# ====================== Tables Model specific Tests ======================

def test_tables_model_initializer():
    mock_address = "dummy.db"

    with patch("model.players_model.SQliteModel.__init__") as mock_super_init, \
         patch.object(TablesModel, "create_table_if_not_exist") as mock_create_table:

        mock_super_init.return_value = None
        instance = TablesModel(mock_address)

        mock_super_init.assert_called_once_with(mock_address, "tables")
        mock_create_table.assert_called_once()