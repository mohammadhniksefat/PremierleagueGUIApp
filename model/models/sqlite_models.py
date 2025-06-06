from pathlib import Path
from model.database_manager import SQliteDatabaseManager
from model.models.base_model import BaseModel, TeamsModel, MatchesModel, PlayersModel, TablesModel
import sqlite3, math

def load_schema(schema_address):
    with open(schema_address) as schema:
        return schema.read()

class SQliteModel(BaseModel):
    schemas = {
        'players' : load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "players.sql"), 
        'teams' : load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "clubs.sql"),
        'matches' : load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "matches.sql"),
        'tables' : load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "tables.sql")
    }

    def __init__(self, database_address, table_name):
        # the cursor and connection will be set in database manager
        self.cursor: sqlite3.Cursor
        self.connection: sqlite3.Connection

        self.database_address = database_address
        self.table_name = table_name

        self.initialize()

    def initialize(self):
        self.unique_constraint: list[str] = self.get_unique_constraint()
        self.column_names = self.get_column_names()
        self.required_columns = self.get_required_column_names()

        db_manager = SQliteDatabaseManager()
        db_manager.configure_model(self)

    def create_table_if_not_exist(self):
        self.cursor.execute(SQliteModel.schemas[self.table_name])

    def get_records(self, **kwargs):

        valid_arguments = {key : value for key, value in kwargs.items() if key in self.column_names}

        if not valid_arguments:
            query = f"SELECT * FROM {self.table_name}"
            self.cursor.execute(query)
        else:
            conditions = " AND ".join(f"{column} = ?" for column in valid_arguments.keys())
            sql = f"SELECT * FROM {self.table_name} WHERE {conditions}"
            self.cursor.execute(sql, tuple(valid_arguments.values()))

        records = self.cursor.fetchall()
        # result = [dict(zip(self.column_names, record)) for record in records]
        result = list(records)
        result.insert(0, self.column_names)
        return records

    def get_specific_column(self, column, key=None):
        """
        Retrieve values from a specific column. If `key` is provided, return a dictionary
        where keys are values from the `key` column and values are from the `column` column.
        
        :param column: The target column to fetch values from.
        :param key: Optional column to use as dictionary keys.
        :return: List of values if key is None, else a dict with key-value mapping.
        """
        valid_columns = self.get_column_names()

        if column not in valid_columns:
            raise ValueError(f"Invalid column: {column}")

        if key is not None and key not in valid_columns:
            raise ValueError(f"Invalid key column: {key}")

        if key:
            query = f"SELECT {key}, {column} FROM {self.table_name}"
            self.cursor.execute(query)
            return {row[0]: row[1] for row in self.cursor.fetchall()}
        else:
            query = f"SELECT {column} FROM {self.table_name}"
            self.cursor.execute(query)
            return [row[0] for row in self.cursor.fetchall()]

    def get_records_count(self):
        """Returns the total number of records in the table."""
        sql = f"SELECT COUNT(*) FROM {self.table_name}"
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]  # Fetch the count

    def create_record(self, dictionary):
        # FIXME make sure that key and value order is identical, I prefer to use OrderedDict class

        """Inserts a new record into the table, ensuring all required columns are provided."""
        if not dictionary:
            raise ValueError("Empty dictionary provided. No data to insert.")

        # Ensure all required columns are in dictionary
        missing_columns = self.required_columns - dictionary.keys()
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        valid_columns = self.get_column_names()

        # Filter valid columns (ignore extra keys)
        filtered_data = {k: v for k, v in dictionary.items() if k in valid_columns}

        # Construct and execute the insert query
        columns = ", ".join(filtered_data.keys())
        placeholders = ", ".join(["?"] * len(filtered_data))
        values = tuple(filtered_data.values())

        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(sql, values)
        self.connection.commit()

    def get_column_names(self):
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        return tuple(row[1] for row in self.cursor.fetchall())

    def get_required_column_names(self):
        """Returns a set of columns that have a NOT NULL constraint."""
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns_info = self.cursor.fetchall()

        # Extract column names where 'notnull' field is 1 (meaning NOT NULL constraint is applied)
        required_columns = tuple(row[1] for row in columns_info if row[3] == 1)

        return required_columns

    def delete_records(self, **kwargs):
        """Deletes records from the table matching the provided keyword arguments and returns the deleted records as dictionaries."""
        if not kwargs:
            raise ValueError("No conditions provided. No records to delete.")
        
        # Get valid columns from the table for validation
        valid_columns = self.get_column_names()

        # Validate that all keys in kwargs are valid columns in the table
        invalid_columns = [key for key in kwargs.keys() if key not in valid_columns]
        if invalid_columns:
            raise ValueError(f"Invalid columns: {', '.join(invalid_columns)}")

        # Fetch the records that will be deleted
        conditions = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        sql_select = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        self.cursor.execute(sql_select, values)
        deleted_records = self.cursor.fetchall()

        # If no records match, return an empty list
        if not deleted_records:
            return []

        # Get column names from the table
        columns = [description[0] for description in self.cursor.description]

        # Convert the fetched records to a list of dictionaries
        deleted_records_dict = [dict(zip(columns, record)) for record in deleted_records]

        # Build the DELETE query
        sql_delete = f"DELETE FROM {self.table_name} WHERE {conditions}"

        # Execute the query
        self.cursor.execute(sql_delete, values)
        self.connection.commit()

        # Return the deleted records as dictionaries
        return deleted_records_dict

    def is_record_exists(self, **kwargs):
        records = self.get_records(**kwargs)
        return bool(records)  # Explicit check for empty list
    
    def get_unique_constraint(self) -> list[str]:
        self.cursor.execute(f"PRAGMA table_info('{self.table_name}')")
        pk_columns = [row[1] for row in self.cursor.fetchall() if row[5] > 0]  # row[5] == pk position

        self.cursor.execute(f"PRAGMA index_list('{self.table_name}')")
        indexes = self.cursor.fetchall()

        unique_constraint = []

        for index in indexes:
            index_name = index[1]
            is_unique = index[2]  # 1 = UNIQUE, 0 = not unique

            if is_unique:
                # Step 2: Get columns in the index
                self.cursor.execute(f"PRAGMA index_info('{index_name}')")
                columns = self.cursor.fetchall()
                column_names = [col[2] for col in columns]  # col[2] is the column name

                if set(column_names) == set(pk_columns):
                    continue

                for column in column_names:
                    unique_constraint.append(column)

        return unique_constraint
    
    def update_record(self, data: dict):
        # Step 1: Check if all unique constraint columns are in the input
        if not all(col in data for col in self.unique_constraint):
            missing = [col for col in self.unique_constraint if col not in data]
            raise ValueError(f"Missing unique constraint fields: {missing}")

        # Step 2: Filter out keys not in column_names
        filtered_data = {k: v for k, v in data.items() if k in self.column_names}

        # Step 3: Find record ID using the unique constraint
        where_clause = " AND ".join(f"{col} = ?" for col in self.unique_constraint)
        where_values = [data[col] for col in self.unique_constraint]

        self.cursor.execute(
            f"SELECT id FROM {self.table_name} WHERE {where_clause}",
            where_values
        )
        result = self.cursor.fetchone()

        if not result:
            raise ValueError("No matching record found for the given unique constraint values.")

        record_id = result[0]

        # Step 4: Remove unique constraint columns and 'id' from data before updating
        update_data = {
            k: v for k, v in filtered_data.items()
            if k not in self.unique_constraint and k != 'id'
        }

        if not update_data:
            raise ValueError("No fields to update after filtering.")

        # Step 5: Generate update statement
        set_clause = ", ".join(f"{k} = ?" for k in update_data)
        values = list(update_data.values()) + [record_id]

        self.cursor.execute(
            f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?",
            values
        )
        
        self.connection.commit()

class PlayersModel(SQliteModel):
    def __init__(self, database_address):
        table_name = 'players'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()

class TeamsModel(SQliteModel):
    def __init__(self, database_address):
        table_name = 'teams'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()

class MatchesModel(SQliteModel):    
    def __init__(self, database_address):
        table_name = 'matches'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()
    
class TablesModel(SQliteModel):
    def __init__(self, database_address):
        table_name = 'tables'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()