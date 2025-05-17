import sqlite3
from . import models
from pathlib import Path

class ModelFactory:
    
    @staticmethod
    def create_model(model, db_address=None):
        if not db_address:
            db_address = str(Path(__file__).parent / "../" / "data" / "main_database.db")

        if DatabaseTypeChecker.check_sqlite_db(db_address):
            if model == 'players':
                return models.sqlite_models.PlayersModel(db_address)
            elif model == 'teams':
                return models.sqlite_models.TeamsModel(db_address)
            elif model == 'matches':
                return models.sqlite_models.MatchesModel(db_address)
            elif model == 'tables':
                return models.sqlite_models.TablesModel(db_address)
        else:
            raise ValueError("invalid database type!")
            
class DatabaseTypeChecker:
    @staticmethod
    def check_sqlite_db(db_address):
        try:
            conn = sqlite3.connect(db_address)
            conn.close()
            return True
        except sqlite3.DatabaseError:
            return False
        

