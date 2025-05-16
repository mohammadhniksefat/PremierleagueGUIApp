from abc import ABC, abstractmethod

class ITablesDataScraper(ABC):
    @abstractmethod
    def initialize(self) -> None:  pass
    
    @abstractmethod
    async def get_tables_data(self) -> list[dict]:  pass