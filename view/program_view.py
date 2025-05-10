import copy, tkinter
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO

from view.matches_section import MatchesSection
from view.tables_section import TablesSection
from view.teams_section import TeamsSection
from view.players_section import PlayersSection

class ProgramWindow:

    def __init__(self, main_callback):
        self.main_callback = main_callback

        self._prepare_window()

    def _prepare_window(self):
        self.root = tkinter.Tk()
        self.root.geometry("700x700")
        self.root.resizable(False, False)
        self.root.title("Premier League App")

        self._create_tabbed_interface()

    def _create_tabbed_interface(self):
        notebook_widget = ttk.Notebook(master=self.root)
        notebook_widget.pack(fill='both', expand=True)

        matches_tab = MatchesSection(notebook_widget, self.main_callback.get_matches_section_callback())
        matches_tab.widget.pack(fill='both', expand=True)
        tables_tab = TablesSection(notebook_widget, self.main_callback.get_tables_section_callback())
        tables_tab.widget.pack(fill='both', expand=True)
        teams_tab = TeamsSection(notebook_widget, self.main_callback.get_teams_section_callback())
        teams_tab.widget.pack(fill='both', expand=True)
        players_tab = PlayersSection(notebook_widget, self.main_callback.get_players_section_callback()) 

        notebook_widget.add(matches_tab.widget, text="Matches")
        notebook_widget.add(tables_tab.widget, text="Tables")
        notebook_widget.add(teams_tab.widget, text="Teams")
        notebook_widget.add(players_tab.widget, text="Players")
        

    def display(self):
        self.root.mainloop()

