CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    short_name TEXT,
    establishment_year INTEGER,
    stadium TEXT,
    manager TEXT,
    page_url TEXT,
    logo BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);