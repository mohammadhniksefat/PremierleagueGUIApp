from model.model_factory import ModelFactory
import controller.commands as commands
import inspect, sys

class TerminalInterface:
    def __init__(self):
        self.commands = self.get_commands()

    def get_commands(self) -> dict[str, type] :
        commands_dict = dict()
        for name, obj in inspect.getmembers(commands):
            if inspect.isclass(obj) and obj.__module__ == commands.__name__:
                if issubclass(obj, commands.ICommand) and obj is not commands.ICommand:
                    commands_dict[obj.base_name] = obj
        return commands_dict

    def run(self):
        while True:
            command_line = input(">> Enter command:\t")

            self.process_command(command_line)

    def process_command(self, command_line):
        parts = command_line.split()
        if not parts:
            print("please enter a command!")
            return
        
        command = parts[0]
        args = parts[1:]

        if command in self.commands.keys():
            # try:
                command_obj = self.commands[command](*args)
                command_obj.execute_command()

            # except ValueError as e:
            #     print(e)

            # except Exception as e:
            #     print(f"unexpected error!\n{type(e)}\t{e}")

        else:
            print(f"unknown command: {command}")

def main():
    interface = TerminalInterface()
    interface.run()


        



    

