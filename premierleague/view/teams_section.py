import tkinter, webbrowser

class TeamsSection:
    def __init__(self, container, callback):
        self.container = container
        self.widget = tkinter.Frame(self.container)
        self.callback = callback
        self.teams_data = self.callback.get_teams_data(logos_width=80)

        self._prepare_section()

    def _prepare_section(self):
        items_in_row = 2
        for index, team_data in enumerate(self.teams_data):
            row_number = int(index / items_in_row)
            column_number = index % items_in_row
            self._create_team_widget(team_data, row_number, column_number)

    def _create_team_widget(self, team_data, row_number, column_number):
        container = tkinter.Frame(self.widget)
        container.grid(row=row_number, column=column_number, padx=6, pady=20)

        heading_part = tkinter.Frame(container)
        heading_part.pack(side='left')
        team_logo = tkinter.Label(heading_part, image=team_data['logo'])
        team_name = tkinter.Label(heading_part, text=team_data['team_name'])
        team_logo.pack(side='top', pady=6, padx=4)
        team_name.pack(side='bottom', pady=6, padx=4)

        information_part = tkinter.Frame(container)
        information_part.pack(side='right', padx=10, pady=5)

        city_name_label = tkinter.Label(information_part, text=f"city: {team_data['city']}")
        city_name_label.pack(side='top', pady=3)

        establishment_year_label = tkinter.Label(information_part, text=f"Establishment Year: {team_data['establishment_year']}")
        establishment_year_label.pack(side='top', pady=3)

        stadium_name_label = tkinter.Label(information_part, text=f"Stadium: {team_data['stadium']}")
        stadium_name_label.pack(side='top', pady=3)

        manager_label = tkinter.Label(information_part, text=f"Manager: {team_data['manager']}")
        manager_label.pack(side='top', pady=3)

        def open_webbrowser_closure(url):
            def func():
                webbrowser.open(url)
            return func

        team_page_link = tkinter.Button(
            information_part,
            text="open Official Page", 
            command=open_webbrowser_closure(team_data['team_page_url'])
        )
        team_page_link.pack(side='top', pady=3)


