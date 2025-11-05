import sqlite3
import logging
from premierleague.model.models import sqlite_models
from pathlib import Path
from premierleague.log_config.logger_configurer import configure_logger

logger = logging.getLogger(__name__)

configure_logger(sqlite_models.__name__)

class ModelFactory:

    @classmethod
    def create_model(cls, table_name, db_address=None):
        logger.debug("Creating model", extra={"tags": ["factory", "create_model"], "table": table_name, "db_address": db_address})

        if not db_address:
            db_address = cls._get_default_db_address()
            logger.info("No DB address provided, using default", extra={"tags": ["factory", "default_db"], "db_address": db_address})

        if DatabaseTypeChecker.check_sqlite_db(db_address):
            models = {
                'players': sqlite_models.PlayersModel,
                'teams': sqlite_models.TeamsModel,
                'matches': sqlite_models.MatchesModel,
                'tables': sqlite_models.TablesModel
            }
            try:
                model_class = models[table_name]
                logger.info("Model class resolved", extra={"tags": ["factory", "resolve_model"], "table": table_name})
                model_instance = model_class(db_address)
                logger.info("Model instance created successfully", extra={"tags": ["factory", "model_created"], "table": table_name})
                return model_instance
            except KeyError as e:
                logger.error("Unknown table name", extra={
                    "tags": ["factory", "error", "invalid_table"],
                    "table": table_name,
                    "error": str(e)
                })
                raise ValueError("Unknown table name!") from e
            except Exception as e:
                logger.error("Unexpected error while creating model", extra={
                    "tags": ["factory", "error", "model_creation"],
                    "table": table_name,
                    "db_address": db_address,
                    "error": str(e)
                })
                raise
        else:
            logger.error("Invalid database type", extra={
                "tags": ["factory", "error", "invalid_db"],
                "db_address": db_address,
                "error": "Not a valid SQLite database"
            })
            raise ValueError("invalid database type!")

    @classmethod
    def _get_default_db_address(cls):
        db_address = str(Path(__file__).parent.parent / "model" / "data" / "main_database.db")
        logger.debug("Resolved default DB address", extra={"tags": ["factory", "default_path"], "db_address": db_address})
        return db_address


class DatabaseTypeChecker:

    @staticmethod
    def check_sqlite_db(db_address):
        logger.debug("Checking if DB is SQLite", extra={"tags": ["db_check", "sqlite"], "db_address": db_address})
        try:
            conn = sqlite3.connect(db_address)
            conn.close()
            logger.info("Database type is valid SQLite", extra={"tags": ["db_check", "sqlite_valid"], "db_address": db_address})
            return True
        except sqlite3.DatabaseError as e:
            logger.warning("Failed to connect as SQLite DB", extra={
                "tags": ["db_check", "sqlite_invalid"],
                "db_address": db_address,
                "error": str(e)
            })
            return False
