# auto-job

A semi-automated job search assistant built with Python.

`auto-job` searches and discovers job sources, normalizes postings into a shared internal model, scores them against configurable preferences, stores results locally, and generates reports/email summaries.

The project focuses on practical backend engineering concepts including:

- API integration
- Data normalization
- ATS discovery
- Scoring/ranking systems
- Local persistence
- Automation workflows
- CLI application architecture

Important:

- `auto-job` does **not** automatically apply to jobs
- Browser automation is intentionally avoided
- Preference is given to APIs, RSS feeds, and ATS boards

---

# Quickstart

Clone the repository, create a virtual environment, and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a local config file:

```bash
cp config.example.yaml config.yaml
```

Verify the install:

```bash
python -m pytest
python -m auto_job.cli config
```

Run a search:

```bash
python -m auto_job.cli search
```

Or run the normal daily workflow with source validation first:

```bash
python -m auto_job.cli run
```

Local runtime files such as `config.yaml`, `.env`, `auto_job.db`, and `reports/` are intentionally ignored by git.

---

# Features

## Multi-Source Job Ingestion

Current supported sources:

- RSS feeds
- RemoteOK API
- Greenhouse boards
- Ashby boards
- Lever postings API

The system normalizes heterogeneous job data into a shared internal `Job` model.

---

## ATS Discovery Pipeline

One of the core goals of the project is reducing the manual work required to discover job sources.

`auto-job` can:

- Detect ATS providers from job URLs/career pages
- Extract provider-specific identifiers
- Register discovered sources into configuration
- Expand source coverage from existing RSS feeds
- Test a maintained company universe against supported ATS providers
- Prune configured company sources that return hard 404s

Current ATS detection support:

- Greenhouse
- Ashby
- Lever

Example discovery flow:

```text
company universe
→ provider slug candidates
→ Greenhouse/Lever/Ashby validation
→ config registration
→ stale source pruning
→ direct ATS ingestion
```

---

## Normalized Job Model

All external job data is converted into a shared internal `Job` model.

Current fields include:

- company
- title
- source
- posting_url
- location
- remote_status
- salary
- date_posted
- description
- description_html
- detected_stack
- match_reasons
- match_score

This creates a normalization boundary between external providers and internal application logic.

`description` is the cleaned plain-text version used for scoring, filtering, and text reports. `description_html` is optional provider HTML that can be sanitized and reused in styled email reports when a source provides reliable markup.

---

## Configurable Scoring System

Jobs are scored using configurable heuristics including:

- Keyword matches
- Title matches
- Preferred technology stack
- Preferred title terms
- Remote status
- Allowed locations
- Title penalties

Hard filters include:

- Excluded keywords
- Remote-only filtering
- Location filtering
- Recency filtering

Example excluded roles:

- senior
- staff
- principal
- architect
- manager

The scoring system intentionally favors transparency and explainability over opaque ranking algorithms.

Example output:

```text
Detected stack: python, postgresql, api
Match reasons: keyword match: backend engineer, preferred stack: python, remote
```

---

## SQLite Persistence

Jobs are stored locally using SQLite.

Features include:

- Database initialization
- Batch inserts
- Deduplication
- Recent job retrieval
- Stored match scores and match explanations

Current deduplication strategy:

```sql
UNIQUE(posting_url)
```

---

## Report Generation

`auto-job` generates readable text reports containing:

- New/seen indicators for each posting
- Match scores
- Source information
- Stack detection
- Match reasoning
- Cleaned job descriptions
- Direct application links

Reports are automatically saved to:

```text
reports/
```

---

## Email Reports

Generated reports can be emailed directly using SMTP.

Current implementation supports:

- Gmail SMTP
- `.env`-based credential loading
- Styled HTML email delivery with plain-text fallback
- New/seen badges based on whether SQLite saved the job for the first time
- Sanitized provider HTML descriptions when available from source adapters

---

## Company Source Discovery

The `discovery` command maintains configured company job sources separately from the daily `run` command. It reads `data/company_universe.yaml`, checks each company slug against Greenhouse, Lever, and Ashby, and reports verified sources.

The current company universe includes hundreds of companies across technology, finance, healthcare, retail, logistics, industrial, media, education, public sector tech, and other categories. This file is intentionally tracked in git because it is curated project data, not personal runtime config.

By default, discovery is a dry run:

```bash
python -m auto_job.cli discovery
```

To write verified new sources and prune configured sources that now return hard 404s:

```bash
python -m auto_job.cli discovery --write --prune-stale
```

Useful options:

- `--limit 100`: test only the first 100 companies in the universe file
- `--providers greenhouse,ashby`: restrict the provider checks
- `--company-file data/company_universe.yaml`: use a different company list
- `--delay 0.2`: slow requests down during larger sweeps

Discovery only auto-adds sources that validate successfully and currently return jobs. Empty boards are not written automatically because they add noise without improving the next job search.

Pruning is conservative. `--prune-stale` validates configured sources in `config.yaml` and removes only exact provider entries that return hard `HTTP 404` responses. It does not remove companies from `data/company_universe.yaml`, and it does not remove empty boards, timeouts, parse failures, or sources that simply have zero jobs today.

RSS-based discovery is still available for URL-driven exploration:

```bash
python -m auto_job.cli discover-from-rss --write
```

---

# CLI Commands

Primary commands:

```bash
python -m auto_job.cli config
python -m auto_job.cli guide
python -m auto_job.cli recent
python -m auto_job.cli search
python -m auto_job.cli validate-sources
python -m auto_job.cli run
python -m auto_job.cli discovery
python -m auto_job.cli discovery --write --prune-stale
python -m auto_job.cli detect-ats <url>
python -m auto_job.cli detect-ats <url> --write
python -m auto_job.cli discover-ats <urls>
python -m auto_job.cli discover-ats <urls> --write
python -m auto_job.cli discover-from-rss
python -m auto_job.cli discover-from-rss --write
```

Primary workflow:

```bash
python -m auto_job.cli run
```

Command summary:

- `config`: print the loaded configuration
- `guide`: print the recommended daily workflow
- `recent`: show recently saved jobs from SQLite
- `search`: fetch, score, store, report, and optionally email matches
- `validate-sources`: check configured RSS, Greenhouse, Lever, and Ashby sources
- `run`: validate sources, then run search, storage, report generation, and optional email delivery
- `discovery`: test the company universe, add verified sources, and optionally prune hard 404s
- `detect-ats`: inspect one URL for a supported ATS provider
- `discover-ats`: inspect multiple URLs for supported ATS providers
- `discover-from-rss`: use configured RSS job URLs as ATS discovery inputs

Commands that support `--write` will update `config.yaml`. Without `--write`, discovery commands are safe inspection tools.

Use `search` when you want to skip validation and go directly to job matching. Use `run --no-validate` for the same full workflow without the validation step.

Use `--limit` with `search` or `run` to control how many matches are printed and included in reports:

```bash
python -m auto_job.cli search --limit 30
python -m auto_job.cli run --limit 30
```

Use `guide` when you want the app to print the recommended command sequence:

```bash
python -m auto_job.cli guide
```

---

# Example Search Pipeline

```text
Configured sources
→ fetch jobs
→ normalize data
→ score/filter jobs
→ dedupe results
→ save to SQLite
→ generate report
→ email report
```

---

# Tech Stack

- Python
- Typer
- Pydantic
- PyYAML
- HTTPX
- SQLite
- feedparser
- Rich
- pytest
- python-dotenv

---

# Project Structure

```text
auto-job/
├── auto_job/
│   ├── ats.py
│   ├── cli.py
│   ├── company_source_discovery.py
│   ├── config.py
│   ├── config_writer.py
│   ├── discovery.py
│   ├── emailer.py
│   ├── job_search.py
│   ├── models.py
│   ├── reporting.py
│   ├── scoring.py
│   ├── storage.py
│   └── sources/
│       ├── ashby.py
│       ├── base.py
│       ├── greenhouse.py
│       ├── lever.py
│       ├── registry.py
│       ├── remoteok.py
│       └── rss.py
├── data/
│   └── company_universe.yaml
├── tests/
├── config.example.yaml
├── requirements.txt
└── README.md
```

Generated local files:

- `config.yaml`: local preferences copied from `config.example.yaml`
- `.env`: optional email password configuration
- `auto_job.db`: local SQLite database
- `reports/`: generated text reports
- `data/generated/`: optional generated discovery exports

---

# Configuration

Create `config.yaml` from the example file:

```bash
cp config.example.yaml config.yaml
```

Example:

```yaml
search:
  keywords:
    - backend engineer
    - software engineer
    - python developer

  locations:
    - united states
    - canada

  remote_only: true
  salary_min: 95000
  recency_days: 7

filters:
  minimum_score: 40

  excluded_keywords:
    - senior
    - staff
    - principal
    - machine learning
    - ml
    - it

  penalty_keywords:
    - intern
    - internship
    - phd intern

  preferred_titles:
    - backend
    - platform
    - product engineer
    - full stack

  preferred_stack:
    - python
    - django
    - postgresql

sources:
  enabled:
    - rss
    - greenhouse
    - ashby
```

Configuration controls:

- `search.keywords`: role and skill terms used for scoring
- `search.locations`: allowed job locations used as a geographic filter
- `search.remote_only`: excludes non-remote jobs when enabled
- `search.recency_days`: excludes old postings when dates are available
- `filters.excluded_keywords`: hard excludes jobs when these words appear in the title
- `filters.penalty_keywords`: subtracts score when these words appear in the title
- `filters.preferred_titles`: adds score when these terms appear in the title
- `filters.preferred_stack`: adds score for preferred technologies
- `filters.minimum_score`: minimum score required before saving/reporting
- `sources.enabled`: source adapters to run during `search`

`config.yaml` is intentionally ignored by git so personal job preferences, target companies, and email settings stay local.

`remote_only` and `search.locations` work together. `remote_only: true` filters out non-remote roles. `search.locations` then limits remote roles to allowed geographies, such as `united states` and `canada`. A generic `remote` location is not treated as an allowed geography by itself, because many boards use it for roles that may be remote outside North America.

Short title filters such as `it`, `ml`, and `sr` match as standalone title terms so they do not accidentally match inside unrelated words. The `senior` exclude also catches common `Sr.` title abbreviations.

---

# Running the Project

## Create a virtual environment

```bash
python -m venv .venv
```

Activate:

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configure the app

Copy:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your preferences.

---

## Configure email support

For Gmail SMTP, `AUTO_JOB_EMAIL_PASSWORD` should be a Google App Password, not your normal Google account password.

Google requires 2-Step Verification before app passwords can be created. See Google's official guide:

```text
https://support.google.com/accounts/answer/185833
```

Create a `.env` file:

```env
AUTO_JOB_EMAIL_PASSWORD=your-app-password
```

Example Gmail settings:

```yaml
email:
  enabled: true
  to: your_email@example.com
  from_email: your_email@example.com
  smtp_host: smtp.gmail.com
  smtp_port: 587
```

---

## Run a search

```bash
python -m auto_job.cli search
```

## Validate sources and run

```bash
python -m auto_job.cli run
```

This validates configured RSS feeds and ATS boards first, then runs the normal search workflow.

Use `--limit` to control how many matches are printed and included in the report/email:

```bash
python -m auto_job.cli run --limit 30
```

To inspect source health without running a search:

```bash
python -m auto_job.cli validate-sources
```

To show only broken or empty sources:

```bash
python -m auto_job.cli validate-sources --problems-only
```

Example validation output:

```text
Source validation:
- rss:https://example.com/jobs.rss (Example Feed): ok, 25 jobs
- greenhouse:exampleco (Example Co): ok, 14 jobs
- lever:missingco (Missing Co): error, 0 jobs - HTTP 404

Validation summary:
- error: 1
- ok: 2
```

Discovery commands validate detected ATS sources before writing them to `config.yaml`. This keeps dead Greenhouse, Lever, or Ashby slugs from being added during company-universe or RSS discovery.

The search output includes source and filtering diagnostics:

```text
Source summary:
- remoteok: fetched 100, matched 2
- rss: fetched 57, matched 0
- greenhouse: fetched 6665, matched 9
- lever: fetched 212, matched 0
- ashby: fetched 1022, matched 2

Filtered out:
- below minimum score: 4300
- excluded keyword: senior: 2100
- outside allowed locations: 1200
- not remote: 900
- too old: 20
```

Use these counts to tune sources, filters, and scoring preferences. For example, a source with many fetched jobs and zero matches may be stale, too noisy, or mismatched with the current search preferences.

---

# Testing

Run all tests:

```bash
python -m pytest
```

Current test coverage includes:

- ATS parsing
- Scoring logic
- Search diagnostics
- Source validation
- CLI write-safety behavior
- Config writing
- SQLite persistence
- Ashby parsing/normalization
- Discovery deduplication
- Company universe discovery, dry-run behavior, config writes, and pruning
- Report formatting, description cleanup, and HTML email structure

Tests are designed to run without a personal `config.yaml`.

---

# Future Improvements

Potential future directions:

- Improved ATS discovery strategies
- Additional ATS providers
- Discovery batching with `--start`/`--offset`
- Discovery failure exports for future provider research
- Better salary normalization
- Source adapter tests with mocked HTTP responses
- Simple SQLite migration/version tracking
- Structured logging
- Scheduled job runs
- Report formatting improvements
- Web dashboard/API layer
- Smarter deduplication strategies

---

# Learning Goals

This project is intentionally being built incrementally to practice:

- Backend architecture
- API integration
- Data normalization
- Scoring/ranking systems
- Local persistence
- CLI application design
- Automation workflows
- Config-driven application structure
- Maintainable Python project organization
- Real-world data ingestion pipelines
