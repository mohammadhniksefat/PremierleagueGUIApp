from model.models import sqlite_models
import sqlite3, atexit

class DatabaseManager:
    pass

class SQliteDatabaseManager(DatabaseManager):
    _instance: SQliteDatabaseManager = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        self._connection = None

    def configure_model(self, model):
        if self._connection is None:
            self._connection = sqlite3.connect(model.database_address)
            self._cursor = self._connection.cursor()

            atexit.register(self.clean_up)

        model.connection = self._connection
        model.cursor = self._cursor

    def clean_up(self):
        self._connection.close()


    