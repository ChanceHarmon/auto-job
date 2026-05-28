import typer
from rich import print

from auto_job.config import load_config
from auto_job.models import Job
from auto_job.storage import get_recent_jobs
from auto_job.job_search import run_job_search
from auto_job.reporting import build_text_report, save_text_report
from auto_job.ats import detect_ats_provider
from auto_job.config_writer import add_provider_source
from auto_job.discovery import discover_ats_from_job_urls, get_discovery_urls_from_jobs
from auto_job.sources.rss import RSSSource
from auto_job.emailer import send_report_email

app = typer.Typer()


@app.command()
def config():
    """Show loaded config."""
    app_config = load_config()

    print("\nLoaded config:\n")

    print(f"Keywords: {app_config.search.keywords}")
    print(f"Remote only: {app_config.search.remote_only}")
    print(f"Sources: {app_config.sources.enabled}")


def print_jobs(jobs: list[Job], limit: int = 10):
    """Print a compact job summary list."""
    for job in jobs[:limit]:
        print(f"[bold]{job.match_score}[/bold] | {job.title} @ {job.company}")
        print(f"[dim]{job.source} | {job.location or 'Unknown location'} | {job.remote_status or 'Unknown remote status'}[/dim]")
        print(f"[link={job.posting_url}]{job.posting_url}[/link]")
        print()


def print_config_snippet(result):
    provider_config = {
        "greenhouse": ("greenhouse_boards", "board_token"),
        "lever": ("lever_companies", "company_slug"),
        "ashby": ("ashby_companies", "company_slug"),
    }

    if result.provider not in provider_config or not result.company_slug:
        return

    config_key, slug_key = provider_config[result.provider]

    print("\nConfig snippet:\n")
    print(f"{config_key}:")
    print(f"  - company: {result.company_slug.title()}")
    print(f"    {slug_key}: {result.company_slug}")


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

    report_path = save_text_report(report)
    print(f"\nSaved report to {report_path}")

    send_report_email(report, app_config)


@app.command()
def detect_ats(url: str):
    """Detect ATS provider from a careers page."""
    result = detect_ats_provider(url)

    if not result:
        print("No known ATS detected")
        return

    print(f"Detected ATS: {result.provider}")
    print(f"Matched pattern: {result.matched_pattern}")
    print(f"ATS URL: {result.ats_url or 'Not found'}")
    print(f"Company slug: {result.company_slug or 'Not found'}")

    print_config_snippet(result)

    if result.company_slug:
        added = add_provider_source(
            "config.yaml",
            result.provider,
            result.company_slug,
        )

        if added:
            print("\nAdded board to config.yaml")
        else:
            print("\nBoard already exists in config.yaml")


@app.command()
def discover_ats(urls: list[str], write: bool = False):
    """Discover ATS providers from job or careers URLs."""
    results = discover_ats_from_job_urls(urls)

    if not results:
        print("No ATS providers discovered")
        return

    for result in results:
        print(f"\nDetected ATS: {result.provider}")
        print(f"ATS URL: {result.ats_url or 'Not found'}")
        print(f"Company slug: {result.company_slug or 'Not found'}")

        if write and result.company_slug:
            added = add_provider_source("config.yaml", result.provider, result.company_slug)

            if added:
                print("Added source to config.yaml")
            else:
                print("Source already exists or unsupported provider")



@app.command()
def discover_from_rss(write: bool = False):
    """Discover ATS providers from configured RSS job URLs."""

    app_config = load_config("config.yaml")
    rss_source = RSSSource(app_config)

    jobs = rss_source.fetch_jobs()
    print(f"Fetched {len(jobs)} RSS jobs")

    urls = get_discovery_urls_from_jobs(jobs)
    print(f"Extracted {len(urls)} URLs")

    results = discover_ats_from_job_urls(urls)
    print(f"Discovered {len(results)} ATS providers")

    if not results:
        print("No ATS providers discovered from RSS jobs")
        return

    added_count = 0
    skipped_count = 0

    for result in results:
        print(f"\nDetected ATS: {result.provider}")
        print(f"ATS URL: {result.ats_url or 'Not found'}")
        print(f"Company slug: {result.company_slug or 'Not found'}")

        if write and result.company_slug:
            added = add_provider_source("config.yaml", result.provider, result.company_slug)

            if added:
                added_count += 1
                print("Added source to config.yaml")
            else:
                skipped_count += 1
                print("Source already exists or unsupported provider")

    if write:
        print(f"\nAdded {added_count} new sources")
        print(f"Skipped {skipped_count} existing/unsupported sources")



if __name__ == "__main__":
    app()
