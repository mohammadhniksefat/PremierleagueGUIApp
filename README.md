# 🏆 Premier League Python GUI Application

A desktop application that scrapes and displays Premier League football data in a user-friendly GUI built with Tkinter.
The application provides structured access to player, club, and match information extracted from the official Premier League website.

⚠️ Note: The scraping functionality may no longer work due to structural changes on the official website (premierleague.com).


## 📋 Overview

This application connects a web scraping system with a graphical interface to present football statistics and information from the Premier League.
It combines automated data collection, validation, and database storage with an intuitive GUI for browsing and viewing the collected data.

---

## ⚙️ Features

Automated Data Scraping — Extracts player, club, and match information directly from the official Premier League website.

Data Validation — Ensures consistency and logs warnings for incomplete or missing data.

Local Database Storage — Stores all extracted data in an SQLite database for offline access.

Graphical Interface (Tkinter) — Displays all stored data with easy navigation between players, clubs, and matches.

Extensible Design — Each module (scraper, database, GUI) is independent, enabling easy maintenance or replacement of individual components.

---

## 🧮 Admin Command-Line Interface

The root of the project includes an admin_controller.py module that provides an interactive command-line interface (CLI) for managing the application and running internal operations.
When launched with:

``` bash
virtualenvironment\scripts\activate
python premierleague\admin_controller.py
```

the program enters an interactive prompt awaiting user commands.
This interface allows administrative control over the scraper, database, and test modules — all from the terminal.

## 💬 Available Commands
Command	Description
help:	Displays all available commands and their descriptions.

db_update:	Updates the local SQLite database by scraping the latest data from the Premier League website and synchronizing it with existing records.

scrape:	Runs the scraper independently and displays the extracted data directly in the terminal for quick inspection.

tests:	Provides an interactive environment to list, select, and execute test modules and test cases from the tests/ directory.

test_request_handler:	Accepts one or more URLs as arguments, sends requests using the project’s RequestHandler class, and returns response summaries for verification.

exit:	Gracefully exits the admin controller.

#### ⚡ Purpose

This CLI serves as a central control hub for:

Quickly updating the database without launching the GUI.

Debugging or verifying scraper performance.

Running and exploring test cases interactively.

Validating network requests and response handling logic.

It provides developers and maintainers with powerful control tools to manage and test every major part of the project.

## 🛠️ Technologies and Libraries
Category	Technologies / Libraries

Language	Python 3

GUI	Tkinter

Web Scraping	BeautifulSoup, Playwright

Database	SQLite3

Testing	Pytest

Logging	Built-in logging module

Architecture	MVC, Modular OOP design (separated extractor, scraper, validator, and DB controller classes)

---

### 🗒️ Notes

The scraping logic may not currently function because the Premier League website structure has changed.

The project serves as a case study in integrating web scraping, data persistence, and GUI presentation within a single Python application.
