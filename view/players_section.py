import tkinter
from tkinter import ttk

class PlayersSection:
    def __init__(self, container, callback):
        self.container = container
        self.callback = callback
        self.players_data_cache = dict()
        self.teams_data = self.callback.get_teams_list(logos_width=25)

        self.widget: tkinter.Frame
        self.teams_list_widget: tkinter.Frame
        self.players_list_frame: tkinter.Frame
        self.active_button: tkinter.Frame

        self._prepare_section()

    def _prepare_section(self):
        self.widget = tkinter.Frame(self.container)

        self._create_teams_list_widget()
        
        self.players_list_frame = tkinter.Frame(self.widget)
        self.players_list_frame.pack(side='top', fill='both', expand=True)

        self._prepare_players_list_widget(self.active_button.team_name)

    def _create_teams_list_widget(self):
        container = tkinter.Frame(self.widget)
        container.pack(side='right', anchor='n', pady=20)

        canvas = tkinter.Canvas(container, bd=0, highlightthickness=0, width=200)
        canvas.pack(side='left')

        self.teams_list_widget = tkinter.Frame(canvas)

        window_id = canvas.create_window(0, 0, window=self.teams_list_widget, anchor='ne')

        scroll_object = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scroll_object.pack(side='right', fill='y')

        canvas.configure(yscrollcommand=scroll_object.set)
        canvas.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        def on_mousewheel(event):
            nonlocal canvas
            canvas.yview_scroll(-1 * (event.delta // 120), 'units')

        def bind_mouswheel(event):
            nonlocal canvas, on_mousewheel
            canvas.bind_all('<MouseWheel>', on_mousewheel)

        def unbind_mousewheel(event):
            canvas.unbind_all("MouseWheel")

        def update_window_position(event):
            canvas.coords(window_id, canvas.winfo_width() - 10, 10)

        canvas.bind("<Enter>", bind_mouswheel)
        canvas.bind("<Leave>", unbind_mousewheel)
        canvas.bind("<Configure>", update_window_position)

        for index, team_data in enumerate(self.teams_data):
            # team_button = tkinter.Frame(self.teams_list_widget, width=50)
            # team_logo = tkinter.Label(team_button, image=team_data['team_logo'])
            # team_logo.pack(side='right')
            # team_name = tkinter.Label(team_button, text=team_data['team_name'])
            # team_name.pack(side='right')

            team_button = ttk.Button(self.teams_list_widget, text=team_data['team_name'], image=team_data['team_logo'], compound='right')
            team_button.pack(side='top', anchor='e', fill='x')
            team_button.configure(command=self._change_team_list_closure(team_data['team_name'], team_button))
            team_button.team_name = team_data['team_name']
            
            # team_button.bind("<Button-1>", self._change_team_list_closure(team_data['team_name'], team_name))

            if index == 0:
                self.active_button = team_button
                self.active_button.state(['pressed'])

            #     team_button.configure(bg='gray')

            
    def _prepare_players_list_widget(self, team_name):
        
        if team_name in self.players_data_cache.keys():
            players_data = self.players_data_cache[team_name]
        else:
            players_data = self.callback.get_players_data(team_name, player_picture_width=40)
            self.players_data_cache[team_name] = players_data
        
        items_in_row = 2

        for position, players_list in players_data.items():
            position_label = tkinter.Label(self.players_list_frame, text=position)
            position_label.pack(side='top', anchor='w')

            players_container = tkinter.Frame(self.players_list_frame)
            players_container.pack(side='top', fill='x')
            for index, player_data in enumerate(players_list):
                row = int(index / items_in_row)
                column = index % items_in_row

                player_widget = tkinter.Frame(players_container)
                player_widget.grid(row=row, column=column, padx=5, pady=5)
                
                heading_part = tkinter.Frame(player_widget)
                heading_part.pack(side='left', pady=15, padx=10)

                player_picture = tkinter.Label(heading_part, image=player_data['player_picture'])
                player_picture.pack(side='top')

                player_name = tkinter.Label(heading_part, text=f'{player_data['firstname']} {player_data['lastname']}')
                player_name.pack(side='top')

                information_part = tkinter.Frame(player_widget)
                information_part.pack(side='right')

                nationality_label = tkinter.Label(information_part, text=f"Nationality: {player_data['nationality']}")
                nationality_label.pack(side='top')

                shirt_number_label = tkinter.Label(information_part, text=f'Number: {player_data['number']}')
                shirt_number_label.pack(side='top')
                
                date_of_birth_label = tkinter.Label(information_part, text=f'Date of Birth: {player_data['date_of_birth']}')
                date_of_birth_label.pack(side='top')

                age_label = tkinter.Label(information_part, text=f'Age: {player_data['age']}')
                age_label.pack(side='top')

                height_label = tkinter.Label(information_part, text=f'Height: {player_data['height']}')
                height_label.pack(side='top')

    def _change_team_list_closure(self, team_name, button):
        def change_team_list():
            nonlocal team_name, button, self
            self.active_button.state(['!pressed'])
            button.state(['pressed'])
            self.active_button = button

            for element in self.players_list_frame.winfo_children():
                element.destroy()

            self._prepare_players_list_widget(team_name)
        

        return change_team_list