import typer
from rich import print

from auto_job.config import load_config
from auto_job.models import Job
from auto_job.sources.demo import DemoSource
from auto_job.storage import get_recent_jobs
from auto_job.job_search import run_job_search
from auto_job.reporting import build_text_report, save_text_report
from auto_job.ats import detect_ats_provider
from auto_job.config_writer import add_greenhouse_board

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


@app.command()
def search():
    """Search enabled job sources, score results, and save matches."""
    app_config = load_config()

    result = run_job_search(app_config)

    print(f"\nMatched {len(result.jobs)} jobs")
    print(f"Saved {result.saved_count} new jobs to SQLite\n")

    print_jobs(result.jobs, 10)

    report = build_text_report(result.jobs)

    save_text_report(report)


@app.command()
def detect_ats(url: str):
    """Detect ATS provider from a careers page."""
    result = detect_ats_provider(url)

    if result:
        print(f"Detected ATS: {result.provider}")
        print(f"Matched pattern: {result.matched_pattern}")
        print(f"ATS URL: {result.ats_url or 'Not found'}")
        print(f"Company slug: {result.company_slug or 'Not found'}")

        if (
            result.provider == "greenhouse"
            and result.company_slug
        ):
            print("\nConfig snippet:\n")

            print("greenhouse_boards:")
            print(f"  - company: {result.company_slug.title()}")
            print(f"    board_token: {result.company_slug}")
            added = add_greenhouse_board(
                "config.yaml",
                result.company_slug.title(),
                result.company_slug,
            )

            if added:
                print("\nAdded board to config.yaml")
            else:
                print("\nBoard already exists in config.yaml")

        elif (
            result.provider == "lever"
            and result.company_slug
        ):
            print("\nConfig snippet:\n")

            print("lever_companies:")
            print(f"  - company: {result.company_slug.title()}")
            print(f"    company_slug: {result.company_slug}")

    else:
        print("No known ATS detected")


if __name__ == "__main__":
    app()
