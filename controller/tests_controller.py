import os
import subprocess
import re

# Base "tests" folder path
base_path = os.path.join(os.path.dirname(__file__), "../tests")
current_path = base_path
last_run_command = None

def is_test_file(filename):
    return filename.startswith("test_") and filename.endswith(".py")

def list_tests_in_module(module_path):
    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return re.findall(r'def (test_\w+)\s*\(', content)

def run_pytest(target):
    global last_run_command
    last_run_command = ["pytest", target]
    subprocess.run(last_run_command)

def main():
    global current_path, last_run_command
    history = []

    while True:
        print(f"\n📁 Current directory: {os.path.relpath(current_path, base_path) or '.'}")
        try:
            entries = os.listdir(current_path)
        except FileNotFoundError:
            print("❌ 'tests' folder not found.")
            return

        test_folders = [e for e in entries if e.startswith("test_") and os.path.isdir(os.path.join(current_path, e))]
        test_files = [e for e in entries if is_test_file(e)]
        all_items = test_folders + test_files

        for i, name in enumerate(all_items):
            item_type = "Folder" if os.path.isdir(os.path.join(current_path, name)) else "Module"
            print(f"{i + 1}. {name} [{item_type}]")

        print("\nOptions:")
        print("a. Run all tests in this directory")
        print("b. Go back" if history else "b. [Top level]")
        print("q. Quit")

        choice = input("\nEnter your choice (number/a/b/q): ").strip()

        if choice == 'q':
            break
        elif choice == 'a':
            run_pytest(current_path)
        elif choice == 'b':
            if history:
                current_path = history.pop()
            else:
                print("Already at top level.")
        elif choice.isdigit() and 1 <= int(choice) <= len(all_items):
            selected = all_items[int(choice) - 1]
            selected_path = os.path.join(current_path, selected)

            if os.path.isdir(selected_path):
                history.append(current_path)
                current_path = selected_path
            else:
                test_cases = list_tests_in_module(selected_path)
                while True:
                    print(f"\n🧪 Test cases in {selected}:")
                    for i, name in enumerate(test_cases):
                        print(f"{i + 1}. {name}")

                    print("\nOptions:")
                    print("a. Run all test cases in this file")
                    print("b. Go back")
                    sub_choice = input("Enter your choice (number/a/b): ").strip()

                    if sub_choice == 'a':
                        run_pytest(selected_path)
                    elif sub_choice == 'b':
                        break
                    elif sub_choice.isdigit() and 1 <= int(sub_choice) <= len(test_cases):
                        test_case = test_cases[int(sub_choice) - 1]
                        test_id = f"{selected_path}::{test_case}"
                        run_pytest(test_id)

                        # Post-test options
                        while True:
                            print("\nPost-test options:")
                            print("a. Repeat last test")
                            print("b. Go back")
                            post_choice = input("Choose (a/b): ").strip()
                            if post_choice == 'a':
                                subprocess.run(last_run_command)
                            elif post_choice == 'b':
                                break

                    else:
                        print("Invalid input.")
        else:
            print("Invalid input.")

if __name__ == "__main__":
    main()
