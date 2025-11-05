from abc import ABC, abstractstaticmethod
from pythonjsonlogger import json
import logging
import importlib
import pkgutil
import types
import os
import sys
from pathlib import Path
from fluent import handler as fluent_handler

ModuleConfigurerRegistery = dict()

ConfiguredLoggers = set()

LoggingLevelsRegistery = {
    'debug': logging.DEBUG, 
    'info': logging.INFO, 
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

LOG_FOLDER_PATH = str(Path(__file__).parent.parent / 'logs')

# LOG_FIELDS = {
#     'asctime': '%(asctime)s',
#     'levelname': '%(levelname)s',
#     'levelno': '%(levelno)s',
#     'name': '%(name)s',
#     'message': '%(message)s',
#     'pathname': '%(pathname)s',
#     'filename': '%(filename)s',
#     'module': '%(module)s',
#     'funcName': '%(funcName)s',
#     'lineno': '%(lineno)d',
#     'created': '%(created)f',
#     'msecs': '%(msecs)d',
#     'relativeCreated': '%(relativeCreated)d',
#     'args': '%(args)s',
#     'exc_info': '%(exc_info)s',
#     'stack_info': '%(stack_info)s',
#     'msg': '%(msg)s'
# }
LOG_FIELDS = {
    'asctime': '%(asctime)s',
    'levelname': '%(levelname)s',
    'message': '%(message)s',
    'pathname': '%(pathname)s',
    'module': '%(module)s',
    'funcName': '%(funcName)s',
    'lineno': '%(lineno)d',
    # 'msg': '%(msg)s'
}

# def register_modules_configurer(scope: str):
#     modules = discover_modules(scope)
#     def decorator(cls):
#         nonlocal modules
#         if issubclass(cls, IConfigurer):
#             registery_update = {module:cls for module in modules}
#             ModuleConfigurerRegistery.update(registery_update)
#         else:
#             raise RuntimeError("class object provided isn't an IConfigurer subclass")

#         return cls
        
#     return decorator

def discover_modules(package_name: str) -> list[types.ModuleType]:
    """Recursively import all modules inside a given package and return their module objects."""
    modules = []
    package = importlib.import_module(package_name)
    
    if not hasattr(package, "__path__"):
        # Not a package, just a module
        return [package]
    
    for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        modules.append(module_info.name)

    return modules

def resolve_module_path(module_name: str):
    module_path = module_name.replace('.', os.sep) + '.json'
    return module_path

def resolve_class_module_name(cls):
    return sys.modules[cls.__module__].__name__

def configure_logger(module_name: str, level:str = 'info', enabled=True):    
    BaseConfigurer.configure_logger(module_name, level, enabled)

class IConfigurer(ABC):
    @abstractstaticmethod
    def configure_logger(module_name: str, level: str='info', enabled: bool=True) -> None: pass

# @register_modules_configurer('premierleague')
class BaseConfigurer(IConfigurer): 
    @staticmethod
    def configure_logger(module_name: str, level: str='info', enabled: bool=True) -> None:
        if module_name not in ConfiguredLoggers:
            logger = logging.getLogger(module_name)
            logger.propagate = False

            if not enabled:
                logger.setLevel(logging.CRITICAL + 1)  # block all messages
                logger.disabled = True
                logger.handlers = []
                return
        
            if level not in LoggingLevelsRegistery.keys():
                raise RuntimeError("invalid logging level provided")
            logger.setLevel(LoggingLevelsRegistery[level])

            log_file_path = LOG_FOLDER_PATH + 'main-log.txt'
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
            file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
            formatter = logging.Formatter(" ".join(LOG_FIELDS.values()))
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)

            ConfiguredLoggers.add(module_name)

def disable_logging():
    logging.disable(logging.CRITICAL)