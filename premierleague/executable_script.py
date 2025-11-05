from controller import user_controller
from view import program_view

def main():
    main_controller = user_controller.MainController()
    window = program_view.ProgramWindow(main_controller)
    window.display()

if __name__ == '__main__':
    main() 