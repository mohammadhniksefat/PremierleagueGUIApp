from model.models import sqlite_models
import sqlite3, atexit

class DatabaseManager:
    pass

class SQliteDatabaseManager(DatabaseManager):
    def configure_model(self, model):
        self._connection = sqlite3.connect(model.database_address)

        model.connection = self._connection
        model.cursor = self._connection.cursor()

        atexit.register(self.clean_up)

    def clean_up(self):
        self._connection.close()