from abc import ABC, abstractmethod

class IPlayerDataScraper(ABC):
    player_data : dict
    
    @abstractmethod
    async def initialize(self) -> None: pass

    @abstractmethod
    async def get_all_data(self) -> dict: pass

    @abstractmethod
    async def get_firstname(self) -> str: pass

    @abstractmethod
    async def get_lastname(self) -> str: pass

    @abstractmethod
    async def get_position(self) -> str: pass

    @abstractmethod
    async def get_nationality(self) -> str: pass

    @abstractmethod
    async def get_shirt_number(self) -> str: pass

    @abstractmethod
    async def get_date_of_birth(self) -> str: pass

    @abstractmethod
    async def get_age(self) -> int: pass

    @abstractmethod
    async def get_height(self) -> int: pass

    @abstractmethod
    async def get_club_name(self) -> str: pass

    @abstractmethod
    async def get_picture(self) -> bytes: pass