from model.model_factory import ModelFactory
import controller.commands as commands
import inspect

def TerminalInterface():
    def __init__(self):
        self.commands = ['help', 'exit']
        self.commands.extend(self.get_commands())

    def get_commands(self):
        commands_dict = dict
        for name, obj in inspect.getmembers(commands):
            if inspect.isclass(obj) and obj.__module__ == commands.__name__:
                if hasattr(obj, 'base_name'):
                    commands_dict[obj.base_name] = obj
        return commands_dict

    def run(self):
        while True:
            command_line = input(">> Enter command:\t")
            if command_line == 'exit':
                print("Exiting...")
                break

            self.process_command(command_line)

    def process_command(self, command_line):
        parts = command_line.split()
        if not parts:
            print("please enter a command!")
            return
        
        command = parts[0]
        args = parts[1:]

        if command == 'help':
            self.execute_help_command()
            return

        if command in self.commands.keys():
            try:
                command_obj = self.commands[command](*args)
                command_obj.execute_command()

            except ValueError as e:
                print(e)

            except Exception as e:
                print("unexpected error!")

        else:
            print(f"unknown command: {command}")

    def execute_help_command(self):
        print('available commands:\n\thelp \n\texit: exit the terminal')
        for command, command_cls in self.commands.values():
            print(f'\t{command}: {command_cls.description}')
    
def main():
    interface = TerminalInterface()
    interface.run()


if __name__ == '__main__':
    main()

        



    

