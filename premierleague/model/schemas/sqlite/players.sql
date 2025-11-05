CREATE TABLE players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_url TEXT NOT NULL,
    name TEXT NOT NULL,
    position TEXT,
    nationality TEXT,
    date_of_birth TEXT,
    shirt_number TEXT,
    club_id INTEGER NOT NULL,
    age INTEGER,
    height INTEGER,
    picture BLOB,

    FOREIGN KEY (club_id) REFERENCES clubs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, date_of_birth)
)