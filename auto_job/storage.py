import sqlite3
from pathlib import Path

from auto_job.models import Job


DB_PATH = Path("auto_job.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                posting_url TEXT NOT NULL UNIQUE,
                location TEXT,
                remote_status TEXT,
                salary TEXT,
                date_posted TEXT,
                description TEXT,
                match_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )