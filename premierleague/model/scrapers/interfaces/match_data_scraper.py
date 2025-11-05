from abc import ABC , abstractmethod
from dataclasses import dataclass

class IMatchDataScraper(ABC):
    match_data : dict

    @abstractmethod
    async def initialize(self) -> None: pass

    @abstractmethod
    async def get_all_data(self) -> dict: pass

    @abstractmethod
    async def get_timestamp(self) -> int: pass

    @abstractmethod
    async def get_home_team_data(self) -> dict: pass

    @abstractmethod
    async def get_away_team_data(self) -> dict: pass

    @abstractmethod
    async def get_referee_name(self) -> str: pass

    @abstractmethod
    async def get_round_number(self) -> int: pass

    
