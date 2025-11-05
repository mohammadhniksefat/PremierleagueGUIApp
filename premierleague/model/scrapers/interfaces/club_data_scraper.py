from abc import ABC, abstractmethod

class IClubDataScraper(ABC):
    club_data : dict
    
    @abstractmethod
    async def initialize(self) -> None: pass

    @abstractmethod
    async def get_all_data(self) -> dict: pass

    @abstractmethod
    async def get_club_name(self) -> str: pass

    @abstractmethod
    async def get_establishment_year(self) -> int: pass

    @abstractmethod
    async def get_manager_name(self) -> str: pass

    @abstractmethod
    async def get_city_name(self) -> str: pass

    @abstractmethod
    async def get_stadium_name(self) -> str: pass

    @abstractmethod
    async def get_squad_page_url(self) -> str: pass

    @abstractmethod
    async def get_club_logo(self) -> bytes: pass