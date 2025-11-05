import sqlite3
import atexit
import logging
from model.models.base_model import BaseModel

logger = logging.getLogger(__name__)

class DatabaseManager():
    pass

class SQliteDatabaseManager(DatabaseManager):
    def configure_model(self, model: BaseModel):
        logger.debug(
            "Entering configure_model method",
            extra={
                "tags": ["debug", "entry", "database", "model_config"],
                "resource": "SQLite database",
                "action": "configure_model"
            }
        )

        try:
            super().__init__()
            logger.debug(
                "Called superclass __init__",
                extra={"tags": ["debug", "superclass_init", "model_config"]}
            )

            db_path = model.database_address
            logger.info(
                f"Connecting to SQLite database at {db_path}",
                extra={
                    "tags": ["info", "database", "connection", "resource_init"],
                    "event_type": "database_connection_start",
                    "resource": db_path,
                    "action": "connect"
                }
            )

            self._connection = sqlite3.connect(db_path)
            logger.debug(
                "SQLite connection established successfully",
                extra={
                    "tags": ["debug", "connection", "database"],
                    "resource": db_path,
                    "action": "connect"
                }
            )

            model.connection = self._connection
            model.cursor = self._connection.cursor()

            logger.info(
                "Model successfully configured with DB connection and cursor",
                extra={
                    "tags": ["info", "model_config", "database"],
                    "event_type": "model_configured",
                    "resource": db_path,
                    "action": "configure"
                }
            )

            atexit.register(self.clean_up)
            logger.debug(
                "Registered clean_up with atexit",
                extra={
                    "tags": ["debug", "atexit", "resource_management"],
                    "event_type": "atexit_register",
                    "resource": db_path
                }
            )

        except sqlite3.Error as e:
            logger.error(
                f"SQLite error occurred while configuring model: {str(e)}",
                exc_info=True,
                extra={
                    "tags": ["error", "database", "sqlite_exception"],
                    "error": str(e),
                    "resource": db_path,
                    "action": "configure_model"
                }
            )
            raise

        except Exception as e:
            logger.critical(
                f"Unexpected error during model configuration: {str(e)}",
                exc_info=True,
                extra={
                    "tags": ["critical", "exception", "unexpected", "model_config"],
                    "error": str(e),
                    "resource": db_path,
                    "action": "configure_model"
                }
            )
            raise

    def clean_up(self):
        logger.debug(
            "Entering clean_up method",
            extra={
                "tags": ["debug", "exit", "resource_cleanup"],
                "event_type": "cleanup_start",
                "resource": "SQLite database",
                "action": "close"
            }
        )

        try:
            self._connection.close()
            logger.info(
                "SQLite connection closed successfully during cleanup",
                extra={
                    "tags": ["info", "cleanup", "database"],
                    "event_type": "resource_cleanup",
                    "resource": "SQLite database",
                    "action": "close"
                }
            )
        except Exception as e:
            logger.error(
                f"Error occurred while closing the database connection: {str(e)}",
                exc_info=True,
                extra={
                    "tags": ["error", "cleanup", "database"],
                    "error": str(e),
                    "resource": "SQLite database",
                    "action": "close"
                }
            )
