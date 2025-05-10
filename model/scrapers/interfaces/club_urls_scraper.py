from abc import ABC, abstractmethod

class IClubUrlsScraper(ABC):
    @abstractmethod
    async def initialize(self) -> None: pass

    @abstractmethod
    async def get_club_urls(self) -> dict[str, str]: pass