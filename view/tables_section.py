import tkinter

class TablesSection:
    def __init__(self, container, callback):
        self.container = container
        self.widget = tkinter.Frame(container, padx=20)
        self.tables_data = callback.get_tables_data()

        self._prepare_section()

    def _prepare_section(self):
        self._create_columns_title_row()
        # self.tables_data.reverse()
        for record in self.tables_data:
            self._create_record_row(record)
        padding_bottom = tkinter.Frame(self.widget)
        padding_bottom.grid(pady=40)

    def _create_columns_title_row(self):

        position_title_container = tkinter.Frame(self.widget)
        position_title_container.grid(row=0, column=0, columnspan=3, sticky='ew', padx=6, pady= 6)
        position_title_label = tkinter.Label(position_title_container, text="Position")
        position_title_label.pack(side='left')
        self.container.columnconfigure(0, weight=3)

        team_title_container = tkinter.Frame(self.widget)
        team_title_container.grid(row=0, column=3, columnspan=5, sticky='ew', padx=15, pady= 8)
        team_title_label = tkinter.Label(team_title_container, text="Team")
        team_title_label.pack(side='left')
        self.container.columnconfigure(1, weight=5)

        played_title_container = tkinter.Frame(self.widget)
        played_title_container.grid(row=0, column=8, columnspan=1, padx=8, pady= 8)
        played_title_label = tkinter.Label(played_title_container, text="Played")
        played_title_label.pack(side='left')
        self.container.columnconfigure(2, weight=1)

        won_title_container = tkinter.Frame(self.widget)
        won_title_container.grid(row=0, column=9, columnspan=1, padx=8, pady= 8)
        won_title_label = tkinter.Label(won_title_container, text="Won")
        won_title_label.pack(side='left')
        self.container.columnconfigure(3, weight=1)

        drawn_title_container = tkinter.Frame(self.widget)
        drawn_title_container.grid(row=0, column=10, columnspan=1, padx=8, pady= 8)
        drawn_title_label = tkinter.Label(drawn_title_container, text="Drawn")
        drawn_title_label.pack(side='left')
        self.container.columnconfigure(4, weight=1)

        lost_title_container = tkinter.Frame(self.widget)
        lost_title_container.grid(row=0, column=11, columnspan=1, padx=8, pady= 8)
        lost_title_label = tkinter.Label(lost_title_container, text="Lost")
        lost_title_label.pack(side='left')
        self.container.columnconfigure(5, weight=1)

        goals_for_title_container = tkinter.Frame(self.widget)
        goals_for_title_container.grid(row=0, column=12, columnspan=1, padx=8, pady= 8)
        goals_for_title_label = tkinter.Label(goals_for_title_container, text="GF")
        goals_for_title_label.pack(side='left')
        self.container.columnconfigure(6, weight=1)

        goals_against_title_container = tkinter.Frame(self.widget)
        goals_against_title_container.grid(row=0, column=13, columnspan=1, padx=8, pady= 8)
        goals_against_title_label = tkinter.Label(goals_against_title_container, text="GA")
        goals_against_title_label.pack(side='left')
        self.container.columnconfigure(7, weight=1)

        goals_difference_title_container = tkinter.Frame(self.widget)
        goals_difference_title_container.grid(row=0, column=14, columnspan=1, padx=8, pady= 8)
        goals_difference_title_label = tkinter.Label(goals_difference_title_container, text="GD")
        goals_difference_title_label.pack(side='left')
        self.container.columnconfigure(8, weight=1)

        points_title_container = tkinter.Frame(self.widget)
        points_title_container.grid(row=0, column=15, columnspan=1, padx=8, pady= 8)
        points_title_label = tkinter.Label(points_title_container, text="Points")
        points_title_label.pack(side='left')
        self.container.columnconfigure(9, weight=1)

    def _create_record_row(self, record):
        position = record['position']

        position_title_container = tkinter.Frame(self.widget)
        position_title_container.grid(row=position, column=0, columnspan=3, sticky='ew', padx=8, pady= 8)
        position_title_label = tkinter.Label(position_title_container, text=f"{position} .")
        position_title_label.pack(side='left')

        team_title_container = tkinter.Frame(self.widget)
        team_title_container.grid(row=position, column=3, columnspan=5, sticky='ew', padx=15, pady= 8)
        team_logo_label = tkinter.Label(team_title_container, image=record["team_logo"])
        team_logo_label.pack(side='left')
        team_title_label = tkinter.Label(team_title_container, text=record["team_name"])
        team_title_label.pack(side='left')

        played_title_container = tkinter.Frame(self.widget)
        played_title_container.grid(row=position, column=8, columnspan=1, padx=8, pady= 8)
        played_title_label = tkinter.Label(played_title_container, text=record["played"])
        played_title_label.pack(side='left')

        won_title_container = tkinter.Frame(self.widget)
        won_title_container.grid(row=position, column=9, columnspan=1, padx=8, pady= 8)
        won_title_label = tkinter.Label(won_title_container, text=record["won"])
        won_title_label.pack(side='left')

        drawn_title_container = tkinter.Frame(self.widget)
        drawn_title_container.grid(row=position, column=10, columnspan=1, padx=8, pady= 8)
        drawn_title_label = tkinter.Label(drawn_title_container, text=record["drawn"])
        drawn_title_label.pack(side='left')

        lost_title_container = tkinter.Frame(self.widget)
        lost_title_container.grid(row=position, column=11, columnspan=1, padx=8, pady= 8)
        lost_title_label = tkinter.Label(lost_title_container, text=record["lost"])
        lost_title_label.pack(side='left')

        goals_for_title_container = tkinter.Frame(self.widget)
        goals_for_title_container.grid(row=position, column=12, columnspan=1, padx=8, pady= 8)
        goals_for_title_label = tkinter.Label(goals_for_title_container, text=record["goals_for"])
        goals_for_title_label.pack(side='left')

        goals_against_title_container = tkinter.Frame(self.widget)
        goals_against_title_container.grid(row=position, column=13, columnspan=1, padx=8, pady= 8)
        goals_against_title_label = tkinter.Label(goals_against_title_container, text=record["goals_against"])
        goals_against_title_label.pack(side='left')

        goals_difference_title_container = tkinter.Frame(self.widget)
        goals_difference_title_container.grid(row=position, column=14, columnspan=1, padx=8, pady= 8)
        goals_difference_title_label = tkinter.Label(goals_difference_title_container, text=record["goals_difference"])
        goals_difference_title_label.pack(side='left')

        points_title_container = tkinter.Frame(self.widget)
        points_title_container.grid(row=position, column=15, columnspan=1, padx=8, pady= 8)
        points_title_label = tkinter.Label(points_title_container, text=record["points"])
        points_title_label.pack(side='left')
