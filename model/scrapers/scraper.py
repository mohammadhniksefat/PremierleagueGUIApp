import json, requests, re, logging
import database_controller 
from functools import wraps
from urllib3.util.retry import Retry
from requests.adaptorrs import HTTPAdaptor


def create_loggers():
    global info_logger, warning_logger

    info_logger = logging.getLogger('InfoLogger')
    info_logger.setLevel(logging.INFO)
    info_logger_handler = logging.FileHandler(r'logs\info.txt')
    info_logger_handler.setLevel(logging.INFO)

    info_logger_formatter = logging.Formatter(
        fmt="{asctime} - {name} - {levelname} - {message}",
        style="{",
    )
    info_logger_handler.setFormatter(info_logger_formatter)
    info_logger.addHandler(info_logger_handler)


    warning_logger = logging.getLogger('warningLogger')
    warning_logger.setLevel(logging.warning)
    warning_handler = logging.FileHandler(r'logs\warnings.txt')
    warning_handler.setLevel(logging.WARNING)

    warning_logger_formatter = logging.Formatter(
        fmt="{asctime} - {name} - {levelname} - {message}",
        style="{",
    )
    warning_handler.setFormatter(warning_logger_formatter)
    warning_logger.addHandler(warning_handler)


if __name__ == "__main__":
    create_loggers()


class Utils:
    def create_session_dec(func):
        def new_func(*args, **kwargs):
            
            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adaptor = HTTPAdaptor(max_retries=retry)
            session.mount('https://', adaptor)
            session.mount('http://', adaptor)

            func(session, *args, **kwargs)

        return new_func
    
    # def extractor_log(first_message, last_message):
    #     def actuall_decorator(func):
    #         def new_func(*args, **kwargs):
    #             logging.debug(first_message)
                
    #             return_value = func(*args, **kwargs)

    #             logging.debug(last_message)

    #             return return_value
    #         return new_func
    #     return actuall_decorator
    

# class LogMessages:

#     def extract_all_clubs_data_log_messages():
#         first_message = "start extracting the data of all clubs"
#         last_message = "end of extracting the data of all clubs"
#         return (first_message, last_message)
    
#     def extract_club_urls_log_messages():
#         first_message = "start extracting all club urls"
#         last_message = "end of extracting all clubs data"
#         return (first_message, last_message)


class LoggingDecorators:
    
    @staticmethod
    def warning_if_none(func):

        def new_func(*args, **kwargs):
            result = func(*args, **kwargs)
            if result.isinstance(str):
                pass

        return new_func


class InputChecker:
    
    @staticmethod
    def check_not_none(func):

        @wraps(func)
        def new_func(*args, **kwargs):
            
            if any(arg is None for arg in args):
                warning_logger.warning(f'input arguments of {func.__name__} is None')
                raise ValueError('input arguments must not be None')
            for key, value in kwargs.items():
                if value is None:
                    raise ValueError(f'"{key}" argument must not be None')
            
            return func(*args, **kwargs)

        return new_func
    
    


class OutputChecker:
    
    @staticmethod
    def check_not_none(func):
        
        @wraps(func)
        def new_func(*args, **kwargs):
            result = func(*args, **kwargs)

            if result is None:
                raise ValueError(f"output of {func.__name__} must not be None")
            return result
        
        return new_func

    @staticmethod            
    def check_not_falsy(func):

        @wraps(func)
        def new_func(*args, **kwargs):
            result = func(*args, **kwargs)

            if not result:
                raise ValueError(f'invalid output for {func.__name__} method')

        return new_func


    def warning_if_not_valid_club_url(func):

        def new_func(*args, **kwargs):

            if not Validator.validate_club_url(*args[1]):
                result = func(*args, **kwargs)

            else:
                pass

            return result

        return new_func
    
    @staticmethod
    def scrap_club_urls_output_check(func):

        @wraps(func)
        def new_func(*args, **kwargs):
            result = func(*args, **kwargs)
            if any(OutputChecker._validate_club_url(url) for url in result.values()):
                raise ValueError(f"invalid output for {func.__name__} method")
            
            return result
        
        return new_func




    

class Scraper:
    
    def __init__(self, url, structure):
        from bs4 import BeautifulSoup as bs
        self.url = url
        self.structure = bs(structure)
    







