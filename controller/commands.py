from abc import ABC, abstractmethod

class ICommand:
    base_name: str
    description: str

    @abstractmethod
    def __init__(self, *args):  pass

    @abstractmethod
    def execute_command(self): pass

class DatabaseUpdate(ICommand):
    base_name = "db_update"
    description = "update database with updated data that scraped from the web"
    
    def __init__(self, *args):
        pass

    def execute_command(self):
        pass