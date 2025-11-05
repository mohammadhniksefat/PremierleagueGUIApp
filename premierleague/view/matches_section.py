import tkinter, datetime
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO

class MatchesSection:
    def __init__(self, master, callback):
        self.master = master
        self.callback = callback
        self.weeks_count = callback.get_weeks_count()
        self.this_week_number = callback.get_this_week_number()
        self.weeks_data_cache = dict()

        self.widget: tkinter.Frame
        self.weeks_list_widget: tkinter.Frame
        self.week_section_container: tkinter.Frame

        self._prepare_section()
        
    def _prepare_section(self):
        self.widget = tkinter.Frame(self.master)
        
        self._create_weeks_list_widget()

        self.week_section_container = tkinter.Frame(self.widget)
        self.week_section_container.pack(side='top', fill='both', pady=20)
        # self.week_section_container.grid(row=0, column=0, columnspan=3)

        this_week_data = self.callback.get_week_data(self.this_week_number)
        # create frame widget as a container for matches section
        
        week_section = WeekSection(self.week_section_container, this_week_data)
        week_section.prepare_section()
        self.weeks_data_cache[self.this_week_number] = week_section
        
    def _create_weeks_list_widget(self):
        container = tkinter.Frame(self.widget)
        container.pack(side='right', anchor="n", pady=20)
        # container.grid(row=0, column=1)

        canvas = tkinter.Canvas(container, width=60)
        canvas.pack(side='left', fill='both', expand=False)

        self.weeks_list_widget = tkinter.Frame(canvas)

        canvas.create_window((0, 0), window=self.weeks_list_widget, anchor="nw")

        scroll_object = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_object.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scroll_object.set)
        canvas.bind('<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        for week_number in range(1, self.weeks_count + 1):
            week_button = tkinter.Button(self.weeks_list_widget, text=f'week {week_number}')
            week_button.configure(command=self.closure(week_number, week_button))

            if week_number == self.this_week_number:
                week_button.configure(fg='lightblue', bg='black')

            week_button.pack(side='bottom', pady=5)

    def change_week(self, week_number, week_button):
        for widget in self.week_section_container.winfo_children():
            widget.destroy()

        if week_number in self.weeks_data_cache.keys():
            self.weeks_data_cache[week_number].prepare_section()
        else:
            new_week_section = WeekSection(self.week_section_container, self.callback.get_week_data(week_number))
            new_week_section.prepare_section()
            self.weeks_data_cache[week_number] = new_week_section

        for button in self.weeks_list_widget.winfo_children():
            button.configure(fg='black', bg='white') # FIXME : fix the colors and replace white with default color

        week_button.configure(fg='lightblue', bg='black')

    def closure(self, week_number, week_button):

            def method():
                nonlocal week_number, week_button
                self.change_week(week_number, week_button)

            return method

class WeekSection:
    def __init__(self, master_widget, week_data):
        self.master = master_widget
        self.data_dict = week_data

    def prepare_section(self):
        for match_date, match_data_list in self.data_dict.items():
            date_container = tkinter.Frame(self.master)
            date_container.pack(side='top', fill='x', pady=5)
            date_label = tkinter.Label(date_container, text=match_date) # FIXME : change title font size and color
            date_label.pack(side='top', fill='x')

            for match_data in match_data_list:
                match_widget = MatchWidget(date_container, match_data)
                match_widget.prepare_widget()

class MatchWidget:
    def __init__(self, master, match_data):
        self.master = master
        self.match_data = match_data

        self.container: tkinter.Frame

    def prepare_widget(self):
        self.container = tkinter.Frame(self.master)
        self.container.pack(side='top', fill='x', padx=10, pady=10)

        home_team_container = tkinter.Frame(self.container)
        home_team_container.pack(side='left')

        home_team_name = self.match_data['home_team_data']['team_name']

        home_team_logo = self.match_data['home_team_data']['logo']

        self._create_team_data_sub_widget(
            home_team_container,
            home_team_name,
            home_team_logo
        )

        self._create_result_sub_widget()

        away_team_container = tkinter.Frame(self.container)
        away_team_container.pack(side='left')

        away_team_name = self.match_data['away_team_data']['team_name']

        away_team_logo = self.match_data['away_team_data']['logo']

        self._create_team_data_sub_widget(
            away_team_container,
            away_team_name,
            away_team_logo,
            reverse=True
        )


    def _create_result_sub_widget(self):
        result_container = tkinter.Frame(self.container)
        result_container.pack(side='left')

        match_timestamp = datetime.datetime.fromtimestamp(self.match_data['timestamp'])
        present_timestamp = datetime.datetime.now()

        is_held = match_timestamp < present_timestamp

        if is_held:
            home_team_score = self.match_data['home_team_data']['score']
            away_team_score = self.match_data['away_team_data']['score']
            label_text = f'{home_team_score} - {away_team_score}'

        else:
            label_text = f'{match_timestamp.hour} : {match_timestamp.minute}'

        label = tkinter.Label(result_container, text=label_text)
        label.pack(fill='both')

    def _create_team_data_sub_widget(self, container, team_name, team_logo, reverse=False):
        team_name_label = tkinter.Label(container, text=team_name)

        logo_widget = tkinter.Label(container, image=team_logo)

        if not reverse:
            team_name_label.pack(side='left')
            logo_widget.pack(side='left')    
        else:
            team_name_label.pack(side='right')
            logo_widget.pack(side='right')

    
