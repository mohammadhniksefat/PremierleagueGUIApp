import logging
import json
import inspect
import sys
import time

from premierleague.model.model_factory import ModelFactory
import premierleague.controller.commands as commands
from premierleague.log_config.logger_configurer import configure_logger, resolve_class_module_name

logger = logging.getLogger(__name__)

configure_logger(resolve_class_module_name(ModelFactory))
configure_logger(commands.__name__)

class TerminalInterface:
    def __init__(self):
        logger.debug("Initializing TerminalInterface", extra={"tags": ["debug", "event", "startup"]})
        self.commands = self.get_commands()
        logger.info("TerminalInterface initialized with commands", extra={
            "tags": ["info", "event"],
            "event_type": "startup",
            "resource": "commands",
            "action": "load",
        })

    def get_commands(self) -> dict[str, type]:
        logger.debug("Scanning available commands in controller.commands", extra={"tags": ["debug", "reflection"]})
        commands_dict = dict()
        for name, obj in inspect.getmembers(commands):
            if inspect.isclass(obj) and obj.__module__ == commands.__name__:
                if issubclass(obj, commands.ICommand) and obj is not commands.ICommand:
                    commands_dict[obj.base_name] = obj
                    logger.debug(f"Command loaded: {obj.base_name}", extra={
                        "tags": ["debug", "reflection", "event"],
                        "event_type": "command_discovered",
                        "resource": obj.base_name
                    })
        return commands_dict

    def run(self):
        logger.info("TerminalInterface run loop started", extra={"tags": ["info", "event"], "event_type": "run_loop"})
        while True:
            try:
                command_line = input(">> Enter command:\t")
                logger.debug("User input received", extra={
                    "tags": ["debug", "access"],
                    "action": "input",
                    "resource": "command_line",
                    "value": command_line
                })
                self.process_command(command_line)
            except KeyboardInterrupt:
                logger.info("Shutdown requested via keyboard interrupt", extra={
                    "tags": ["info", "shutdown"],
                    "event_type": "shutdown"
                })
                break
            except Exception as e:
                logger.critical("Unexpected system failure", extra={
                    "tags": ["critical", "exception"],
                    "error": f"{type(e).__name__}: {e}",
                    "event_type": "run_loop_failure"
                })
                break

    def process_command(self, command_line):
        parts = command_line.split()
        if not parts:
            logger.warning("Empty command received", extra={
                "tags": ["warning", "validation"],
                "field": "command_line",
                "value": command_line,
                "result": "failed"
            })
            print("please enter a command!")
            return

        command = parts[0]
        args = parts[1:]

        logger.debug("Processing command", extra={
            "tags": ["debug", "processing"],
            "action": "parse",
            "resource": command,
            "value": args
        })

        if command in self.commands.keys():
            try:
                logger.info("Executing command", extra={
                    "tags": ["info", "event"],
                    "action": "execute",
                    "resource": command
                })

                command_obj = self.commands[command](*args)
                command_obj.execute_command()

                logger.info("Command executed successfully", extra={
                    "tags": ["info", "event", "success"],
                    "action": "execute",
                    "resource": command
                })

            except Exception as e:
                logger.error("Command execution failed", extra={
                    "tags": ["error", "exception"],
                    "error": f"{type(e).__name__}: {e}",
                    "action": "execute",
                    "resource": command
                })
                print(f"unexpected error!\n{type(e)}\t{e}")
        else:
            logger.warning("Unknown command received", extra={
                "tags": ["warning", "validation"],
                "field": "command",
                "value": command,
                "result": "failed"
            })
            print(f"unknown command: {command}")


def main():
    logger.info("Main entry point reached", extra={"tags": ["info", "startup"], "event_type": "start_app"})
    interface = TerminalInterface()
    interface.run()
