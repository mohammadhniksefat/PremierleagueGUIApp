from model.model_factory import ModelFactory

def TerminalInterface():
    def __init__(self):
        self.commands = {
            "update_database": self.update_database,
            "search": self.search_in_database,
            "create_tables": database_controller.create_tables,
            "list": self.print_commands_list
        }

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

        if command in self.commands.keys():
            try:
                self.commands[command](*args)

            except ValueError as e:
                print(e)

            except Exception as e:
                print("unexpected error!")

        else:
            print(f"unknown command: {command}")

    def update_database(self, table):
        if not table:
            raise ValueError("table name not specified!")
        
        tables = database_controller.get_tables_list()
        if table not in tables:
            raise ValueError(f"unknown table name: {table}")

        model_controller.update_database(table)

    def search_in_database(self, table, column, value):
        result = database_controller.search_in_database(table, column, value)
        
        for record, counter in result, range(1, len(result) + 1):
            print(f"{counter}:")
            
            for key, value in record.items():
                print(f"    {key}: {value}")
            
            print()

    def print_commands_list(self):
        print("update_database <table_name> : extract updated data and overwrite it on existing data in database")
        print("search <table_name> <column name> <value to be searched> : search for records in specified table that has specified value on specified column")
        print("create_tables : create tables if they not exist")

    
def main():
    interface = TerminalInterface()
    interface.run()


if __name__ == '__main__':
    main()

        



    

