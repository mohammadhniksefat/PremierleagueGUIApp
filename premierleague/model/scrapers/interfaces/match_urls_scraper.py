from abc import ABC, abstractmethod

class IMatchUrlsScraper(ABC):
    @abstractmethod
    async def initialize(self) -> None: pass

    @abstractmethod
    async def get_match_urls(self) -> dict[int, list[str]]: pass