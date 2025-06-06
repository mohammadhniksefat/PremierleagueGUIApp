CREATE TABLE IF NOT EXISTS matches(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        home_team_id INTEGER NOT NULL,
        home_team_data TEXT NOT NULL,
        away_team_id INTEGER NOT NULL,
        away_team_data TEXT NOT NULL,
        referee TEXT,
        match_week INTEGER NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (home_club_id) REFERENCES clubs(id),
        FOREIGN KEY (away_club_id) REFERENCES clubs(id)
        UNIQUE (home_team_id, away_team_id)
)
