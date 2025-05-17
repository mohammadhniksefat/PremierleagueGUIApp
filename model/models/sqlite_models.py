from model.models import base_model
from pathlib import Path
from model.database_manager import SQliteDatabaseManager
from model.models.base_model import BaseModel
import sqlite3, math

def load_schema(schema_address):
    with open(schema_address) as schema:
        return schema.read()

class SQliteModel(BaseModel):
    schemas = {
        'players' : load_schema(Path(__file__).parent / ".." / "schemas" / "sqlite" / "players_table.sql"), 
        'teams' : load_schema(Path(__file__).parent / ".." / "schemas" / "sqlite" / "teams_table.sql"),
        'matches' : load_schema(Path(__file__).parent / ".." / "schemas" / "sqlite" / "matches_table.sql"),
        'tables' : load_schema(Path(__file__).parent / ".." / "schemas" / "sqlite" / "tables_table.sql")
    }

    def __init__(self, database_address, table_name):
        # the cursor and connection will be set in database manager
        self.cursor: sqlite3.Cursor
        self_connection: sqlite3.Connection

        self.database_address = database_address
        self.table_name = table_name
        self.unique_constraint: list[str] = self.get_unique_constraint()
        self.column_names = self.get_column_names()
        self.required_columns = self.get_required_column_names()

        db_manager = SQliteDatabaseManager()
        db_manager.configure_model(self)

    def create_table_if_not_exist(self):
        self.cursor.execute(SQliteModel.schemas[self.table_name])

    def get_records(self, **kwargs):
        
        table_columns = self.get_table_columns()

        valid_arguments = {key : value for key, value in kwargs.items() if key in table_columns}

        if not valid_arguments:
            query = f"SELECT * FROM {self.table_name}"
            self.cursor.execute(query)
        else:
            conditions = " AND ".join(f"{column} = ?" for column in valid_arguments.keys())
            sql = f"SELECT * FROM {self.table_name} WHERE {conditions}"
            self.cursor.execute(sql, tuple(valid_arguments.values()))

        return self.cursor.fetchall()

    def get_specific_column(self, column, sort_by=None):
        """Retrieve a specific column from the table, optionally sorting the results."""
        # Validate the column and sort_by to prevent SQL injection
        valid_columns = self.get_table_columns()
        
        if column not in valid_columns:
            raise ValueError(f"Invalid column: {column}")
        
        if sort_by and sort_by not in valid_columns:
            raise ValueError(f"Invalid sort column: {sort_by}")

        # Build the SQL query
        sql = f"SELECT {column} FROM {self.table_name}"
        if sort_by:
            sql += f" ORDER BY {sort_by}"

        # Execute query and return results
        self.cursor.execute(sql)
        return self.cursor.fetchall()

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

        # Get all columns and required columns
        required_columns = self.get_required_columns()

        # Ensure all required columns are in dictionary
        missing_columns = required_columns - dictionary.keys()
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        valid_columns = self.get_table_columns()

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
        return {row[1] for row in self.cursor.fetchall()}
    
    def get_required_column_names(self):
        """Returns a set of columns that have a NOT NULL constraint."""
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns_info = self.cursor.fetchall()

        # Extract column names where 'notnull' field is 1 (meaning NOT NULL constraint is applied)
        required_columns = {row[1] for row in columns_info if row[3] == 1}

        return required_columns
    
    def delete_records(self, **kwargs):
        """Deletes records from the table matching the provided keyword arguments and returns the deleted records as dictionaries."""
        if not kwargs:
            raise ValueError("No conditions provided. No records to delete.")
        
        # Get valid columns from the table for validation
        valid_columns = self.get_table_columns()

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
        return self.get_records(**kwargs) is not None
    
    def get_table_unique_constraint(self) -> list[str]:
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

class PlayersModel(SQliteModel, base_model.PlayersModel):
    def __init___(self, database_address):
        table_name = 'players'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()

class TeamsModel(SQliteModel, base_model.TeamsModel):
    def __init___(self, database_address):
        table_name = 'teams'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()

    def get_team_id_by_its_name(self, team_name):
        # SQL query to find the team ID by team name
        self.cursor.execute("SELECT id FROM teams WHERE team_name = ?", (team_name,))
        result = self.cursor.fetchone()  # Fetch the first matching row
        
        if result:
            return result[0]  # The 'id' column is the first element in the row
        else:
            return None  # If no team with the given name is found

class MatchesModel(SQliteModel, base_model.MatchesModel):    
    def __init___(self, database_address):
        table_name = 'matches'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()

    def get_records_within_period(self, timestamp, period):
        if period == 'week':
            database = self.get_records()
            timestamps_list = [record['timestamp'] for record in database]

            timestamp = timestamp
            last_index = len(timestamps_list)
            first_index = closest_index = 0

            while True:
                minimum_timestamp = timestamps_list[first_index]
                maximum_timestamp = timestamps_list[last_index]

                a_day_seconds = 24 * 60 * 60 
                if timestamp - minimum_timestamp < a_day_seconds:
                    closest_index = first_index + 1
                    break
                elif maximum_timestamp - timestamp < a_day_seconds or last_index - first_index == 1:
                    closest_index = last_index
                    break

                middle_index = math.ceil(last_index/2)
                if abs(timestamp - minimum_timestamp) < abs(maximum_timestamp - timestamp):
                    last_index = middle_index
                else:
                    first_index = middle_index
            
            week_number = database[closest_index]['week_number']
            filtered_records = list(filter(lambda record: record['week_number'] == week_number, database))
            return filtered_records

    def update_record(self, data):
        pass
    
class TablesModel(SQliteModel, base_model.TablesModel):
    def __init___(self, database_address):
        table_name = 'tables'
        super().__init__(database_address, table_name)
        self.create_table_if_not_exist()