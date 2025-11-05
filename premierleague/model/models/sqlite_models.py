import logging
import json
import sqlite3
from pathlib import Path
from model.database_manager import SQliteDatabaseManager
from model.models.base_model import BaseModel
from log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)
configure_logger(resolve_class_module_name(SQliteDatabaseManager))


def load_schema(schema_address):
    try:
        logger.debug("Loading schema", extra={
            "tags": ["debug", "filesystem"],
            "resource": str(schema_address),
            "event_type": "load_schema",
            "status": "start"
        })
        with open(schema_address) as schema:
            schema_content = schema.read()
            logger.info("Schema loaded", extra={
                "tags": ["info", "filesystem"],
                "resource": str(schema_address),
                "event_type": "schema_loaded",
                "status": "success"
            })
            return schema_content
    except Exception as e:
        logger.critical("Failed to load schema", extra={
            "tags": ["critical", "filesystem", "exception"],
            "resource": str(schema_address),
            "event_type": "schema_load_failed",
            "status": "error",
            "error": str(e)
        })
        raise


class SQliteModel(BaseModel):
    schemas = {
        'players': load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "players.sql"),
        'teams': load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "clubs.sql"),
        'matches': load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "matches.sql"),
        'tables': load_schema(Path(__file__).parent.parent / "schemas" / "sqlite" / "tables.sql")
    }

    def __init__(self, database_address, table_name):
        self.cursor: sqlite3.Cursor
        self.connection: sqlite3.Connection
        self.database_address = database_address
        self.table_name = table_name

        logger.info(f"Initializing SQliteModel for table '{table_name}'", extra={
            "tags": ["init", "database"],
            "event_type": "model_init",
            "resource": table_name,
            "status": "start"
        })

        self.initialize()

    def initialize(self):
        logger.debug("Calling initialize()", extra={
            "tags": ["debug", "lifecycle"],
            "resource": self.table_name,
            "event_type": "initialize_start"
        })
        try:
            self.unique_constraint: list[str] = self.get_unique_constraint()
            self.column_names = self.get_column_names()
            self.required_columns = self.get_required_column_names()
            db_manager = SQliteDatabaseManager()
            db_manager.configure_model(self)
            logger.info(f"Model initialized for table '{self.table_name}'", extra={
                "tags": ["event", "lifecycle"],
                "event_type": "model_initialized",
                "resource": self.table_name,
                "status": "success"
            })
        except Exception as e:
            logger.error("Initialization failed", extra={
                "tags": ["error", "exception", "init"],
                "resource": self.table_name,
                "event_type": "model_init_failed",
                "status": "error",
                "error": str(e)
            })
            raise

    def create_table_if_not_exist(self):
        logger.debug(f"Creating table '{self.table_name}' if not exists", extra={
            "tags": ["sql", "schema"],
            "resource": self.table_name,
            "event_type": "create_table_check"
        })
        try:
            self.cursor.execute(SQliteModel.schemas[self.table_name])
            logger.info(f"Table '{self.table_name}' checked/created", extra={
                "tags": ["schema", "info"],
                "event_type": "table_create_check",
                "resource": self.table_name,
                "status": "success"
            })
        except Exception as e:
            logger.error("Table creation failed", extra={
                "tags": ["exception", "schema"],
                "event_type": "create_table_failed",
                "error": str(e),
                "resource": self.table_name,
                "status": "error"
            })
            raise

    def get_records(self, **kwargs):
        logger.debug("Fetching records", extra={
            "tags": ["database", "read"],
            "resource": self.table_name,
            "event_type": "get_records_start"
        })
        valid_arguments = {key: value for key, value in kwargs.items() if key in self.column_names}
        try:
            if not valid_arguments:
                query = f"SELECT * FROM {self.table_name}"
                logger.debug("Executing: SELECT *", extra={
                    "tags": ["debug", "sql"],
                    "resource": self.table_name,
                    "query_type": "unfiltered"
                })
                self.cursor.execute(query)
            else:
                conditions = " AND ".join(f"{column} = ?" for column in valid_arguments)
                sql = f"SELECT * FROM {self.table_name} WHERE {conditions}"
                logger.debug(f"Executing filtered query: {sql}", extra={
                    "tags": ["debug", "sql"],
                    "resource": self.table_name,
                    "query_type": "filtered",
                    "filters": valid_arguments
                })
                self.cursor.execute(sql, tuple(valid_arguments.values()))

            records = self.cursor.fetchall()
            logger.info("Records fetched", extra={
                "tags": ["database", "info"],
                "resource": self.table_name,
                "event_type": "records_fetched",
                "status": "success",
                "rows": len(records)
            })
            result = [dict(list(zip(self.column_names, record))) for record in records]
            
            return result
            
        except Exception as e:
            logger.error("Failed to fetch records", extra={
                "tags": ["error", "exception", "database"],
                "resource": self.table_name,
                "event_type": "get_records_failed",
                "status": "error",
                "error": str(e)
            })
            raise

    def get_specific_column(self, column, key=None):
        logger.debug("Fetching specific column", extra={
            "tags": ["debug", "database"],
            "field": column,
            "resource": self.table_name,
            "event_type": "get_column_start"
        })
        valid_columns = self.get_column_names()
        if column not in valid_columns:
            logger.warning("Invalid column requested", extra={
                "tags": ["validation", "warning"],
                "field": column,
                "result": "fail",
                "resource": self.table_name,
                "event_type": "invalid_column"
            })
            raise ValueError(f"Invalid column: {column}")
        if key and key not in valid_columns:
            logger.warning("Invalid key column requested", extra={
                "tags": ["validation", "warning"],
                "field": key,
                "result": "fail",
                "resource": self.table_name,
                "event_type": "invalid_key"
            })
            raise ValueError(f"Invalid key column: {key}")

        query = f"SELECT {key}, {column} FROM {self.table_name}" if key else f"SELECT {column} FROM {self.table_name}"
        self.cursor.execute(query)
        result = {row[0]: row[1] for row in self.cursor.fetchall()} if key else [row[0] for row in self.cursor.fetchall()]
        logger.info("Specific column fetched", extra={
            "tags": ["info", "database"],
            "resource": self.table_name,
            "event_type": "column_fetched",
            "field": column,
            "status": "success"
        })
        return result

    def get_records_count(self):
        logger.debug("Counting records", extra={
            "tags": ["debug", "count"],
            "resource": self.table_name,
            "event_type": "count_records"
        })
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = self.cursor.fetchone()[0]
            logger.info("Record count retrieved", extra={
                "tags": ["info", "metrics"],
                "resource": self.table_name,
                "event_type": "count_success",
                "result": count
            })
            return count
        except Exception as e:
            logger.error("Failed to count records", extra={
                "tags": ["error", "exception"],
                "resource": self.table_name,
                "event_type": "count_failed",
                "error": str(e)
            })
            raise

    def create_record(self, dictionary):
        logger.debug("Creating new record", extra={
            "tags": ["debug", "insert"],
            "resource": self.table_name,
            "event_type": "create_start"
        })
        if not dictionary:
            logger.warning("Empty dictionary received for insert", extra={
                "tags": ["validation", "warning"],
                "result": "fail",
                "event_type": "create_validation_empty"
            })
            raise ValueError("Empty dictionary provided. No data to insert.")

        missing_columns = set(self.required_columns) - set(dictionary.keys())
        if missing_columns:
            logger.warning("Missing required columns", extra={
                "tags": ["validation", "error"],
                "field": list(missing_columns),
                "result": "fail",
                "resource": self.table_name,
                "event_type": "create_validation_missing"
            })
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        filtered_data = {k: v for k, v in dictionary.items() if k in self.column_names}
        try:
            sql = f"INSERT INTO {self.table_name} ({', '.join(filtered_data)}) VALUES ({', '.join(['?'] * len(filtered_data))})"
            self.cursor.execute(sql, tuple(filtered_data.values()))
            self.connection.commit()
            logger.info("Record inserted", extra={
                "tags": ["database", "insert"],
                "resource": self.table_name,
                "event_type": "create_success",
                "inserted_fields": list(filtered_data.keys()),
                "status": "success"
            })
        except Exception as e:
            logger.error("Failed to insert record", extra={
                "tags": ["exception", "insert"],
                "error": str(e),
                "resource": self.table_name,
                "event_type": "create_failed",
                "status": "error"
            })
            raise
        
    def delete_records(self, **kwargs):
        logger.debug("Entering delete_records method", extra={"tags": ["debug", "access"], "action": "delete", "resource": self.table_name})
        
        if not kwargs:
            logger.error("No conditions provided for deletion", extra={
                "tags": ["validation", "error"],
                "result": "fail",
                "resource": self.table_name
            })
            raise ValueError("No conditions provided. No records to delete.")
        
        invalid_columns = [key for key in kwargs if key not in self.column_names]
        if invalid_columns:
            logger.error("Invalid columns for deletion", extra={
                "tags": ["validation", "error"],
                "field": invalid_columns,
                "result": "fail",
                "resource": self.table_name
            })
            raise ValueError(f"Invalid columns: {', '.join(invalid_columns)}")

        conditions = " AND ".join([f"{key} = ?" for key in kwargs])
        values = tuple(kwargs.values())
        sql_select = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        
        logger.debug("Executing SELECT before deletion", extra={
            "tags": ["debug", "sql"],
            "resource": self.table_name,
            "action": "select_before_delete"
        })
        
        self.cursor.execute(sql_select, values)
        deleted_records = self.cursor.fetchall()

        if not deleted_records:
            logger.warning("No matching records found for deletion", extra={
                "tags": ["warning", "database"],
                "resource": self.table_name,
                "action": "delete"
            })
            return []

        sql_delete = f"DELETE FROM {self.table_name} WHERE {conditions}"
        self.cursor.execute(sql_delete, values)
        self.connection.commit()
        
        logger.info("Records deleted", extra={
            "tags": ["info", "database", "delete"],
            "resource": self.table_name,
            "action": "delete",
            "result": "success"
        })

        return [dict(list(zip(self.column_names, record))) for record in deleted_records]

    def update_record(self, data: dict):
        logger.debug("Entering update_record method", extra={
            "tags": ["debug", "access"],
            "action": "update",
            "resource": self.table_name
        })

        if not all(col in data for col in self.unique_constraint):
            missing = [col for col in self.unique_constraint if col not in data]
            logger.error("Missing unique constraint columns", extra={
                "tags": ["validation", "error"],
                "field": missing,
                "result": "fail",
                "resource": self.table_name
            })
            raise ValueError(f"Missing unique constraint fields: {missing}")

        filtered_data = {k: v for k, v in data.items() if k in self.column_names}
        logger.debug("Filtered update data", extra={
            "tags": ["debug", "transformation"],
            "field": list(filtered_data.keys()),
            "resource": self.table_name
        })

        where_clause = " AND ".join(f"{col} = ?" for col in self.unique_constraint)
        self.cursor.execute(f"SELECT id FROM {self.table_name} WHERE {where_clause}", [data[col] for col in self.unique_constraint])
        result = self.cursor.fetchone()

        if not result:
            logger.warning("No matching record to update", extra={
                "tags": ["warning", "database"],
                "resource": self.table_name,
                "action": "update"
            })
            raise ValueError("No matching record found for the given unique constraint values.")

        record_id = result[0]
        update_data = {k: v for k, v in filtered_data.items() if k not in self.unique_constraint and k != 'id'}

        if not update_data:
            logger.error("No fields to update", extra={
                "tags": ["validation", "error"],
                "result": "fail",
                "resource": self.table_name
            })
            raise ValueError("No fields to update after filtering.")

        set_clause = ", ".join(f"{k} = ?" for k in update_data)
        values = list(update_data.values()) + [record_id]

        logger.debug("Executing UPDATE statement", extra={
            "tags": ["debug", "sql"],
            "action": "update",
            "resource": self.table_name,
            "field": list(update_data.keys())
        })

        self.cursor.execute(f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?", values)
        self.connection.commit()

        logger.info("Record updated successfully", extra={
            "tags": ["info", "database", "update"],
            "resource": self.table_name,
            "action": "update_record",
            "result": "success"
        })

    def get_column_names(self):
        logger.debug("Fetching column names", extra={"tags": ["debug", "schema"], "resource": self.table_name})
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        return tuple(row[1] for row in self.cursor.fetchall())

    def get_required_column_names(self):
        logger.debug("Fetching required column names", extra={"tags": ["debug", "schema"], "resource": self.table_name})
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        return tuple(row[1] for row in self.cursor.fetchall() if row[3] == 1)

    def is_record_exists(self, **kwargs):
        exists = bool(self.get_records(**kwargs))
        logger.debug("Checked if record exists", extra={
            "tags": ["debug", "exist_check"],
            "result": exists,
            "resource": self.table_name
        })
        return exists

    def get_unique_constraint(self) -> list[str]:
        logger.debug("Getting unique constraints", extra={"tags": ["debug", "schema"], "resource": self.table_name})
        self.cursor.execute(f"PRAGMA table_info('{self.table_name}')")
        pk_columns = [row[1] for row in self.cursor.fetchall() if row[5] > 0]

        self.cursor.execute(f"PRAGMA index_list('{self.table_name}')")
        indexes = self.cursor.fetchall()
        unique_constraint = []

        for index in indexes:
            if index[2]:  # is unique
                self.cursor.execute(f"PRAGMA index_info('{index[1]}')")
                column_names = [col[2] for col in self.cursor.fetchall()]
                if set(column_names) != set(pk_columns):
                    unique_constraint.extend(column_names)

        logger.debug("Fetched unique constraints", extra={
            "tags": ["debug", "schema"],
            "field": unique_constraint,
            "resource": self.table_name
        })
        return unique_constraint


class PlayersModel(SQliteModel):
    def __init__(self, database_address):
        super().__init__(database_address, 'players')
        self.create_table_if_not_exist()

class TeamsModel(SQliteModel):
    def __init__(self, database_address):
        super().__init__(database_address, 'teams')
        self.create_table_if_not_exist()

class MatchesModel(SQliteModel):    
    def __init__(self, database_address):
        super().__init__(database_address, 'matches')
        self.create_table_if_not_exist()

class TablesModel(SQliteModel):
    def __init__(self, database_address):
        super().__init__(database_address, 'tables')
        self.create_table_if_not_exist()
