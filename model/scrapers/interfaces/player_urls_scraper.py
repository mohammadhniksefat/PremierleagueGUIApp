from abc import ABC, abstractmethod

class IPlayerUrlsScraper(ABC):
    @abstractmethod
    async def initialize(self) -> None: pass
    
    @abstractmethod
    async def get_club_player_urls(self, club_name=None, club_url=None) -> list[str]: pass