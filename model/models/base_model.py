from abc import ABC, abstractmethod

class BaseModel(ABC):    
    @abstractmethod
    def create_table_if_not_exist(self): pass

    @abstractmethod
    def get_records(self): pass

    @abstractmethod
    def get_specific_column(self, column, key=None): pass

    @abstractmethod
    def get_records_count(self): pass

    @abstractmethod
    def is_record_exist(self): pass

    @abstractmethod
    def delete_records(self): pass

    @abstractmethod
    def create_record(self, record): pass

    @abstractmethod
    def get_column_names(self): pass

    @abstractmethod
    def get_required_column_names(self): pass

    @abstractmethod
    def get_unique_constraint(self) -> list[str]: pass

class TeamsModel(BaseModel, ABC):
    pass

class MatchesModel(BaseModel, ABC):
    @abstractmethod
    def get_records_within_period(self, timestamp, period): pass

class PlayersModel(BaseModel, ABC):
    pass

class TablesModel(BaseModel, ABC):
    pass