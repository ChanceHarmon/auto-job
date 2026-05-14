import typer
from rich import print

from auto_job.config import load_config
from auto_job.models import Job
from auto_job.sources.demo import DemoSource
from auto_job.sources.remoteok import RemoteOKSource
from auto_job.scoring import score_job
from auto_job.storage import init_db, save_jobs
from auto_job.storage import get_recent_jobs
from auto_job.job_search import (
    fetch_jobs_from_sources,
    score_and_filter_jobs,
)
from auto_job.reporting import build_text_report, save_text_report

app = typer.Typer()


@app.command()
def config():
    """Show loaded config."""
    app_config = load_config()

    print("\nLoaded config:\n")

    print(f"Keywords: {app_config.search.keywords}")
    print(f"Remote only: {app_config.search.remote_only}")
    print(f"Sources: {app_config.sources.enabled}")


@app.command()
def demo_job():
    """Create and display a sample normalized job."""
    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="demo",
        posting_url="https://example.com/jobs/backend-engineer",
        location="Remote",
        remote_status="remote",
        description="Python, APIs, PostgreSQL"
    )

    print(job)


@app.command()
def demo_source():
    """Fetch jobs from the demo source."""
    app_config = load_config()

    source = DemoSource(app_config)

    jobs = source.fetch_jobs()

    print(f"\nFetched {len(jobs)} jobs:\n")

    for job in jobs:
        print(f"{job.title} @ {job.company}")
        print(f"Source: {job.source}")
        print(f"URL: {job.posting_url}")
        print()


def print_jobs(jobs: list[Job], limit: int = 10):
    """Print a compact job summary list."""
    for job in jobs[:limit]:
        print(f"[bold]{job.match_score}[/bold] | {job.title} @ {job.company}")
        print(f"[dim]{job.source} | {job.location or 'Unknown location'} | {job.remote_status or 'Unknown remote status'}[/dim]")
        print(f"[link={job.posting_url}]{job.posting_url}[/link]")
        print()


@app.command()
def recent(limit: int = 10):
    """Show recent saved jobs."""

    jobs = get_recent_jobs(limit)

    print(f"\nShowing {len(jobs)} saved jobs:\n")

    print_jobs(jobs, limit)


def dedupe_jobs(jobs: list[Job]) -> list[Job]:
    """Remove duplicate jobs by company/title, keeping the highest score."""
    unique_jobs = {}

    for job in jobs:
        key = (
            job.company.lower().strip(),
            job.title.lower().strip(),
        )

        existing_job = unique_jobs.get(key)

        if existing_job is None or job.match_score > existing_job.match_score:
            unique_jobs[key] = job

    return list(unique_jobs.values())


@app.command()
def search():
    """Search enabled job sources, score results, and save matches."""
    app_config = load_config()

    jobs = fetch_jobs_from_sources(app_config)

    all_scored_jobs = score_and_filter_jobs(jobs, app_config)

    all_scored_jobs = dedupe_jobs(all_scored_jobs)

    all_scored_jobs.sort(
        key=lambda job: job.match_score,
        reverse=True
    )

    init_db()
    saved_count = save_jobs(all_scored_jobs)

    print(f"\nMatched {len(all_scored_jobs)} jobs")
    print(f"Saved {saved_count} new jobs to SQLite\n")

    report = build_text_report(all_scored_jobs)

    print("\nReport Preview:\n")
    print(report)

    report_path = save_text_report(report)

    print(f"\nSaved report to {report_path}\n")



if __name__ == "__main__":
    app()
