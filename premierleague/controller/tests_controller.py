import os
import subprocess
import re
import logging
import traceback
from datetime import datetime
from log_config.logger_configurer import configure_logger

logger = logging.getLogger(__name__)

# Base "tests" folder path
base_path = os.path.join(os.path.dirname(__file__), "../tests")
current_path = base_path
last_run_command = None

def is_test_file(filename):
    result = filename.startswith("test_") and filename.endswith(".py")
    logger.debug("Checked if file is test file", extra={
        "tags": ["validation", "debug"],
        "field": "filename",
        "value": filename,
        "result": result
    })
    return result

def list_tests_in_module(module_path):
    logger.info("Listing test functions in module", extra={
        "tags": ["event", "access"],
        "action": "list_test_cases",
        "resource": module_path,
        "event_type": "parse_test_file"
    })
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        test_functions = re.findall(r'def (test_\w+)\s*\(', content)
        logger.debug("Parsed test functions from file", extra={
            "tags": ["debug"],
            "resource": module_path,
            "value": test_functions
        })
        return test_functions
    except Exception as e:
        logger.error("Failed to list test functions", extra={
            "tags": ["exception", "error"],
            "resource": module_path,
            "error": traceback.format_exc()
        })
        return []

def run_pytest(target):
    global last_run_command
    last_run_command = ["pytest", target]
    logger.info("Running pytest", extra={
        "tags": ["event", "execution"],
        "action": "run_pytest",
        "resource": target,
        "event_type": "run_tests"
    })
    try:
        subprocess.run(last_run_command)
        logger.info("pytest finished", extra={
            "tags": ["event"],
            "resource": target,
            "event_type": "test_run_complete"
        })
    except Exception as e:
        logger.error("Pytest run failed", extra={
            "tags": ["exception", "error"],
            "resource": target,
            "error": traceback.format_exc()
        })

def main():
    global current_path, last_run_command
    history = []

    logger.info("Test browser started", extra={
        "tags": ["event"],
        "event_type": "startup"
    })

    while True:
        logger.debug("Current navigation path", extra={
            "tags": ["debug", "access"],
            "resource": current_path
        })

        print(f"\n📁 Current directory: {os.path.relpath(current_path, base_path) or '.'}")
        try:
            entries = os.listdir(current_path)
        except FileNotFoundError:
            logger.warning("'tests' folder not found", extra={
                "tags": ["access", "warning"],
                "resource": current_path
            })
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
        logger.debug("User input received", extra={
            "tags": ["debug", "access"],
            "field": "choice",
            "value": choice
        })

        if choice == 'q':
            logger.info("User chose to quit", extra={
                "tags": ["event"],
                "event_type": "shutdown"
            })
            break
        elif choice == 'a':
            run_pytest(current_path)
        elif choice == 'b':
            if history:
                previous = current_path
                current_path = history.pop()
                logger.info("Navigated back", extra={
                    "tags": ["event", "navigation"],
                    "action": "go_back",
                    "resource": previous
                })
            else:
                print("Already at top level.")
                logger.warning("User tried to go back from top level", extra={
                    "tags": ["validation", "warning"],
                    "action": "go_back",
                    "result": "failed"
                })
        elif choice.isdigit() and 1 <= int(choice) <= len(all_items):
            selected = all_items[int(choice) - 1]
            selected_path = os.path.join(current_path, selected)
            logger.info("User selected item", extra={
                "tags": ["event", "access"],
                "action": "select_item",
                "resource": selected_path
            })

            if os.path.isdir(selected_path):
                history.append(current_path)
                current_path = selected_path
                logger.debug("Entered subdirectory", extra={
                    "tags": ["navigation", "debug"],
                    "resource": current_path
                })
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
                    logger.debug("User input (test case menu)", extra={
                        "tags": ["debug", "access"],
                        "field": "sub_choice",
                        "value": sub_choice
                    })

                    if sub_choice == 'a':
                        run_pytest(selected_path)
                    elif sub_choice == 'b':
                        break
                    elif sub_choice.isdigit() and 1 <= int(sub_choice) <= len(test_cases):
                        test_case = test_cases[int(sub_choice) - 1]
                        test_id = f"{selected_path}::{test_case}"
                        logger.info("Running individual test case", extra={
                            "tags": ["event", "execution"],
                            "action": "run_test_case",
                            "resource": test_id
                        })
                        run_pytest(test_id)

                        while True:
                            print("\nPost-test options:")
                            print("a. Repeat last test")
                            print("b. Go back")
                            post_choice = input("Choose (a/b): ").strip()
                            logger.debug("User input (post-test menu)", extra={
                                "tags": ["debug", "access"],
                                "field": "post_choice",
                                "value": post_choice
                            })
                            if post_choice == 'a':
                                logger.info("Repeating last test", extra={
                                    "tags": ["event", "execution"],
                                    "action": "repeat_last_test",
                                    "resource": last_run_command
                                })
                                subprocess.run(last_run_command)
                            elif post_choice == 'b':
                                break
                    else:
                        print("Invalid input.")
                        logger.warning("Invalid sub-choice input", extra={
                            "tags": ["validation", "warning"],
                            "field": "sub_choice",
                            "value": sub_choice,
                            "result": "failed"
                        })
        else:
            print("Invalid input.")
            logger.warning("Invalid main menu input", extra={
                "tags": ["validation", "warning"],
                "field": "choice",
                "value": choice,
                "result": "failed"
            })

if __name__ == "__main__":
    configure_logger(__name__)
    main()
