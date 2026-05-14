import sqlite3
from pathlib import Path
from datetime import date

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


def save_job(job: Job) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO jobs (
                company,
                title,
                source,
                posting_url,
                location,
                remote_status,
                salary,
                date_posted,
                description,
                match_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.company,
                job.title,
                job.source,
                str(job.posting_url),
                job.location,
                job.remote_status,
                job.salary,
                job.date_posted.isoformat() if job.date_posted else None,
                job.description,
                job.match_score,
            ),
        )

        return cursor.rowcount > 0


def save_jobs(jobs: list[Job]) -> int:
    saved_count = 0

    for job in jobs:
        was_saved = save_job(job)

        if was_saved:
            saved_count += 1

    return saved_count


def get_recent_jobs(limit: int = 20) -> list[Job]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                company,
                title,
                source,
                posting_url,
                location,
                remote_status,
                salary,
                date_posted,
                description,
                match_score
            FROM jobs
            ORDER BY match_score DESC, created_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    jobs = []

    for row in rows:
        date_posted = (
            date.fromisoformat(row[7])
            if row[7]
            else None
        )

        job = Job(
            company=row[0],
            title=row[1],
            source=row[2],
            posting_url=row[3],
            location=row[4],
            remote_status=row[5],
            salary=row[6],
            date_posted=date_posted,
            description=row[8],
            match_score=row[9],
        )

        jobs.append(job)

    return jobs