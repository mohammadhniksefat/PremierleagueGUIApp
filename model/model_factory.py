import sqlite3
from model.models import sqlite_models
from pathlib import Path

class ModelFactory:
    
    @classmethod
    def create_model(cls, table_name, db_address=None):
        if not db_address:
            db_address = cls._get_default_db_address()

        if DatabaseTypeChecker.check_sqlite_db(db_address):
            models = {
                'players': sqlite_models.PlayersModel,
                'teams': sqlite_models.TeamsModel,
                'matches': sqlite_models.MatchesModel,
                'tables': sqlite_models.TablesModel
            }
            try:
                return models[table_name](db_address)
            except KeyError:
                raise ValueError("Unknown table name!")
        else:
            raise ValueError("invalid database type!")
        
    @classmethod
    def _get_default_db_address(cls):
        db_address = str(Path(__file__).parent.parent / "model" / "data" / "main_database.db")
        return db_address
            
class DatabaseTypeChecker:
    @staticmethod
    def check_sqlite_db(db_address):
        try:
            conn = sqlite3.connect(db_address)
            conn.close()
            return True
        except sqlite3.DatabaseError:
            return False      