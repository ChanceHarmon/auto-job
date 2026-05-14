# auto-job

A semi-automated job search assistant built with Python.

`auto-job` searches job sources, normalizes job postings into a shared format, scores them against configurable preferences, and stores matching results locally for review.

This project is focused on backend architecture, APIs, automation, data normalization, and practical job-search tooling.

## Goals

The long-term goal is to build a workflow that can:

*   Search multiple job sources
*   Normalize job posting data
*   Score and rank jobs against user preferences
*   Filter out unwanted roles
*   Store results locally
*   Generate reports or email summaries

Important:

*   This project does **not** automatically apply to jobs
*   Browser automation is intentionally avoided for now
*   Preference is given to APIs, RSS feeds, and lightweight respectful scraping

* * *

# Current Features

## YAML Configuration

Uses:

*   PyYAML
*   Pydantic

Configuration supports:

*   Search keywords
*   Preferred locations
*   Remote-only filtering
*   Salary minimums
*   Recency filtering
*   Excluded keywords
*   Preferred technology stack
*   Enabled sources
*   Placeholder email settings

Example:

```
search:
  keywords:
    - backend engineer
    - software engineer

filters:
  minimum_score: 40

  excluded_keywords:
    - senior
    - staff
```

* * *

## Normalized Job Model

All external job data is converted into a shared internal `Job` model.

Current fields include:

*   company
*   title
*   source
*   posting\_url
*   location
*   remote\_status
*   salary
*   date\_posted
*   description
*   detected\_stack
*   match\_score

This creates a normalization boundary between external job sources and internal application logic.

* * *

## Source Adapter Architecture

Each source implements a shared abstract interface.

Current structure:

```
sources/
├── base.py
├── demo.py
├── registry.py
└── remoteok.py
```

Current source support:

*   RemoteOK API

The architecture is designed so additional adapters can be added later with minimal changes to the rest of the system.

* * *

## Scoring System

Jobs are scored based on:

*   Keyword matches
*   Title matches
*   Preferred technology stack
*   Remote status

Jobs containing excluded keywords are rejected before scoring.

Examples of excluded roles:

*   senior
*   staff
*   principal
*   architect
*   manager

The scoring system is intentionally heuristic-based and configurable.

* * *

## SQLite Persistence

Jobs are stored locally using SQLite.

Current implementation uses Python's built-in `sqlite3` module.

Features include:

*   Database initialization
*   Batch saving
*   Deduplication
*   Recent job retrieval

Deduplication is currently handled with:

    UNIQUE(posting_url)

* * *

## CLI Commands

The project currently uses Typer for the command-line interface.

Available commands:

```
python -m auto_job.cli config
python -m auto_job.cli demo-job
python -m auto_job.cli demo-source
python -m auto_job.cli remoteok
python -m auto_job.cli recent
python -m auto_job.cli search
```

Primary workflow:

`python -m auto_job.cli search`

* * *

# Tech Stack

*   Python
*   Typer
*   Pydantic
*   PyYAML
*   HTTPX
*   SQLite
*   Rich

* * *

# Project Structure

```
auto-job/
│
├── auto_job/
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── scoring.py
│   ├── storage.py
│   │
│   └── sources/
│       ├── base.py
│       ├── demo.py
│       ├── registry.py
│       └── remoteok.py
│
├── README.md
├── config.example.yaml
└── auto_job.db
```

* * *

# Running the Project

## Create a virtual environment

`python -m venv .venv`

Activate:

macOS/Linux:

`source .venv/bin/activate`

Windows:

`.venv\Scripts\activate`

* * *

## Install dependencies

`pip install -r requirements.txt`

* * *

## Configure the app

Copy:

`cp config.example.yaml config.yaml`

Edit `config.yaml` with your preferences.

* * *

## Run a search

`python -m auto_job.cli search`

* * *

# Future Improvements

Planned improvements include:

*   Additional job sources
*   RSS feed support
*   Improved scoring heuristics
*   Better deduplication
*   Email reports
*   Scheduled runs
*   Structured logging
*   Automated tests
*   SQLAlchemy migration evaluation
*   Web dashboard or API layer

* * *

# Learning Goals

This project is intentionally being built incrementally to practice:

*   Backend architecture
*   API integration
*   Data normalization
*   Scoring/ranking systems
*   Local persistence
*   CLI application design
*   Automation workflows
*   Maintainable Python project structure