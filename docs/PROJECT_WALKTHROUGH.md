# Auto-Job Project Walkthrough

This document is a talking-points guide for explaining how Auto-Job works. It is intentionally different from the README: the README is for setup and usage, while this file is for remembering the architecture, design decisions, and interview-level tradeoffs.

---

# High-Level Pitch

Auto-Job is a local-first job search assistant. It pulls job postings from multiple job sources, normalizes them into one internal model, scores them against configurable preferences, stores matches in SQLite, and generates a text/email report.

The project does not apply to jobs automatically. It focuses on source ingestion, normalization, ranking, persistence, reporting, and lightweight source discovery.

Good summary:

> Auto-Job is a Python CLI that turns scattered job boards into a local, ranked job feed based on configurable preferences.

---

# Main Workflow

The normal command is:

```bash
python -m auto_job.cli run
```

That command does four main things:

1. Validates configured sources.
2. Fetches jobs from enabled source adapters.
3. Scores, filters, deduplicates, and saves matches.
4. Generates a text report and optionally sends a styled HTML email.

The flow looks like this:

```text
config.yaml
  -> validate sources
  -> fetch jobs from enabled adapters
  -> normalize into Job models
  -> score and filter
  -> dedupe by company/title
  -> save new matches to SQLite
  -> generate report
  -> optionally email styled report
```

---

# Core Design Decisions

## Local-First

The app stores data locally in SQLite and keeps private config out of git. This is intentional because job search preferences, target companies, and email settings are personal.

Why this matters:

- No hosted service is required.
- The app can be run from a terminal.
- The database and reports stay on the user's machine.
- It keeps the project portfolio-friendly without needing auth, accounts, or deployment.

## Normalized Job Model

Every source returns different data. Greenhouse, Ashby, Lever, RemoteOK, and RSS all shape postings differently.

The `Job` model in `auto_job/models.py` is the boundary:

```text
external provider data -> source adapter -> Job model -> scoring/storage/reporting
```

Once a posting is converted into a `Job`, the rest of the app does not need to know which provider it came from.

Talking point:

> The source adapters isolate provider-specific parsing. Scoring and reporting only depend on the normalized internal model.

## Config-Driven Preferences

The app uses `config.yaml` for preferences instead of hardcoding job-search logic.

Important config areas:

- `search.keywords`: broad role/search intent.
- `search.locations`: allowed geography.
- `search.remote_only`: filters non-remote jobs.
- `filters.excluded_keywords`: hard title excludes.
- `filters.penalty_keywords`: soft title penalties.
- `filters.preferred_titles`: title boosts.
- `filters.preferred_stack`: technology boosts.
- `sources.enabled`: which adapters to run.

This keeps the code reusable while allowing the user to adjust search behavior quickly.

---

# Important Files

## `auto_job/cli.py`

This is the Typer CLI entry point.

Main commands:

- `run`: validates sources, searches, saves, reports, and emails.
- `search`: searches without the validation step.
- `validate-sources`: checks configured source health.
- `discovery`: tests the company universe, writes verified sources, and optionally prunes hard 404s.
- `discover-from-rss`: uses RSS jobs as seeds for ATS discovery.
- `detect-ats`: checks one URL for Greenhouse, Lever, or Ashby.
- `recent`: shows saved jobs.
- `guide`: prints the recommended workflow.

The CLI intentionally stays thin. It mostly loads config, calls application helpers, and prints user-facing progress.

## `auto_job/config.py`

Defines the Pydantic config models.

This gives the app typed access to config values and makes malformed config easier to catch.

## `auto_job/models.py`

Defines the normalized `Job` model.

This is one of the most important design pieces because every source adapter feeds into it.

## `auto_job/job_search.py`

Coordinates the search pipeline:

- fetch from sources
- score/filter
- count diagnostics
- dedupe
- sort
- save to SQLite

It returns `JobSearchResult`, which includes both matches and diagnostic counts for CLI output.

## `auto_job/scoring.py`

Contains ranking and filtering logic.

The scoring order is:

1. Hard filters.
2. Keyword/title matches.
3. Preferred stack boosts.
4. Preferred title boosts.
5. Penalties.
6. Remote boost.

Hard filters return score `0` immediately. Boosts and penalties keep the job in play but change ranking.

Important distinction:

- Excluded keywords remove jobs.
- Penalty keywords lower score.
- Preferred titles raise score.

## `auto_job/storage.py`

Handles SQLite persistence.

The `posting_url` column is unique, so repeated runs do not create duplicate saved jobs.

The storage layer also preserves scoring explanations:

- `detected_stack`
- `match_reasons`
- `match_score`

## `auto_job/reporting.py`

Builds the plain-text report.

Reporting has two output paths:

- plain text saved to the `reports/` directory
- styled HTML sent as the email body, with plain text as fallback

Description snippets prefer useful sections such as required qualifications, qualifications, and responsibilities when available.

Each report entry is marked as new or seen. That value comes from SQLite insert behavior: if the posting URL was inserted during this run, it is new; if SQLite ignored it because the URL already existed, it was previously discovered.

## `auto_job/emailer.py`

Sends the report through SMTP.

Credentials are not stored in config. The Gmail app password is read from the `AUTO_JOB_EMAIL_PASSWORD` environment variable.

## `auto_job/source_validation.py`

Checks whether configured sources are alive and returning postings.

This helps identify bad slugs, stale companies, empty boards, or request failures before running the full search.

## `auto_job/ats.py`

Detects supported ATS providers from URLs or page HTML.

Supported providers:

- Greenhouse
- Lever
- Ashby

It extracts provider identifiers such as board tokens or company slugs.

## `auto_job/discovery.py`

Turns job URLs into ATS discovery candidates.

The current discovery strategy is deliberately conservative:

- use existing RSS jobs as discovery seeds
- detect supported ATS providers
- dedupe provider/slug pairs
- validate before writing to config

## `auto_job/company_source_discovery.py`

Maintains configured company job sources from a curated company universe.

This is separate from the daily search flow because it can make many network calls. The command:

- reads `data/company_universe.yaml`
- tests candidate slugs against Greenhouse, Lever, and Ashby
- adds only sources that validate and currently return jobs
- optionally prunes configured company sources that now return hard `HTTP 404`

Empty boards are not auto-added or auto-pruned. That choice keeps the command conservative: an empty board can be real but temporarily useless, while a hard 404 usually means the slug is wrong or the company moved.

---

# Source Adapter Strategy

Each source adapter subclasses `JobSource` and returns a list of normalized `Job` objects.

## RSS

RSS is broad and lightweight. It is also useful for discovery because RSS postings often link to company job pages.

## RemoteOK

RemoteOK has a public API. The source skips the metadata row and normalizes salary, tags, date, and job URL.

## Greenhouse

Greenhouse has a structured board API. The adapter loops through configured board tokens and fetches full job content. It stores both cleaned plain text for matching and the original provider HTML so email reports can preserve the posting's headings, paragraphs, and lists after sanitization.

## Lever

Lever has a postings API. The adapter combines split fields like description, lists, and closing text into one description.

## Ashby

Ashby requires more parsing. The board page exposes listing data, and individual posting pages provide richer descriptions. The adapter fetches descriptions concurrently to keep runtime reasonable.

---

# Scoring Explained

Scoring is intentionally transparent. The app records `match_reasons` so a user can see why a job ranked where it did.

Example reasons:

```text
keyword match: backend engineer
title match: software engineer
preferred stack: python
preferred title: platform
remote
```

Hard filter examples:

```text
excluded keyword: senior
not remote
outside allowed locations
too old
```

The goal is not perfect ranking. The goal is to surface a useful short list while keeping the logic easy to understand and tune.

---

# Diagnostics

The search output includes:

- source fetch counts
- source match counts
- deduped match count
- filter reason counts

This helps answer questions like:

- Which sources are noisy?
- Which filters are removing most jobs?
- Are sources broken or just low quality?
- Are good jobs being filtered too aggressively?

---

# Testing Strategy

Tests are split by responsibility:

- `test_scoring.py`: ranking, hard filters, penalties, title matching.
- `test_job_search.py`: source match counts and filter diagnostics.
- `test_storage.py`: SQLite persistence.
- `test_reporting.py`: report formatting and description snippets.
- `test_ats.py`: ATS detection and slug extraction.
- `test_discovery.py`: deduping discovery results.
- `test_company_source_discovery.py`: company-universe discovery, dry-run safety, writes, and pruning.
- `test_config_writer.py`: safe config writes.
- `test_source_validation.py`: source health checks.
- source-specific tests: Greenhouse-like behavior is covered through search/validation, while Ashby, Lever, and RemoteOK have direct adapter tests.

Most tests avoid real network calls by monkeypatching HTTP calls or using small fake responses.

Talking point:

> I tried to keep tests close to behavior: source parsing, scoring rules, persistence, and CLI safety.

---

# Strong Interview Talking Points

## Normalization Boundary

Different external APIs are normalized into one `Job` model before scoring and reporting.

Why it matters:

- reduces provider-specific branching
- makes new sources easier to add
- keeps scoring independent from source implementation

## Configurable Scoring

Search preferences live in config, not code.

Why it matters:

- easier to tune daily
- demonstrates separation between logic and user preference
- avoids hardcoded one-off rules

## Local Persistence

SQLite stores matched jobs and avoids duplicates with a unique posting URL.

Why it matters:

- repeated runs are safe
- local-first architecture keeps private job data local
- simple persistence layer is appropriate for project size

## Operational Feedback

The CLI prints validation, source, and filter diagnostics.

Why it matters:

- users can see progress during long runs
- failed sources are visible
- filter counts help tune config

## Respectful Discovery

Discovery is based on known company names, guessed ATS slugs, existing links, and known ATS patterns, not broad scraping.

Why it matters:

- avoids brittle or aggressive scraping
- validates discovered sources before writing them
- keeps the system maintainable

---

# Tradeoffs

## Why Not a Frontend Yet?

The core value is in ingestion, scoring, reporting, and automation. A frontend could be added later, but the CLI already supports the main workflow.

## Why Not Auto-Apply?

Auto-applying would add risk, privacy concerns, and low-quality applications. This project helps discover and rank jobs; the user still decides where to apply.

## Why Not Store Application Status?

The current user workflow uses an external tracker. Adding application management would duplicate that workflow and make the app less focused.

## Why Plain Text Plus HTML Email?

Plain text works well for saved local reports because it is easy to search and diff. HTML is better for email because it can use larger text, spacing, links, and new/seen badges while still keeping a plain-text fallback.

---

# Good Future Improvements

The most meaningful future work would be:

- Better ATS/source discovery.
- Additional provider support if a stable public pattern exists.
- Better salary parsing and normalization.
- More intelligent description section extraction.
- Source quality summaries from real run data.
- Larger curated company universe with more industries and slug variants.

Less urgent:

- frontend dashboard
- deployment
- application tracking
- complex ML ranking

---

# One-Minute Explanation

Auto-Job is a Python CLI that automates the boring parts of searching across multiple job sources. It reads a local YAML config, fetches jobs from RSS, RemoteOK, Greenhouse, Lever, and Ashby, normalizes every posting into one Pydantic `Job` model, scores and filters jobs against configurable preferences, saves matches in SQLite, and generates a report that can be emailed with styled HTML and plain-text fallback. It also has source validation plus company-universe discovery, so new Greenhouse, Lever, and Ashby sources can be found, checked, written to config, and conservatively pruned when they go stale. The main engineering focus is clean boundaries: source adapters handle provider-specific data, scoring handles ranking, storage handles persistence, and the CLI coordinates the workflow.
