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
from auto_job.source_validation import validate_discovery_result, validate_sources

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


def print_search_diagnostics(result):
    """Print source and filtering summaries for a search run."""
    print("\nSource summary:")

    for source_name, fetched_count in result.source_fetch_counts.items():
        matched_count = result.source_match_counts.get(source_name, 0)
        print(f"- {source_name}: fetched {fetched_count}, matched {matched_count}")

    if result.deduped_count:
        print(f"- deduped matches: {result.deduped_count}")

    if result.filter_counts:
        print("\nFiltered out:")

        for reason, count in sorted(
            result.filter_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(f"- {reason}: {count}")


def print_source_validation_results(results, problems_only: bool = False):
    print("\nSource validation:")

    if not results:
        print("- no configured sources to validate")
        return

    visible_results = [
        result
        for result in results
        if not problems_only or result.status != "ok"
    ]

    if not visible_results:
        print("- no source problems found")
    for result in visible_results:
        details = f"{result.provider}:{result.identifier}"
        message = f" - {result.message}" if result.message else ""
        print(
            f"- {details} ({result.company}): "
            f"{result.status}, {result.job_count} jobs{message}"
        )

    status_counts = {}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1

    print("\nValidation summary:")
    for status, count in sorted(status_counts.items()):
        print(f"- {status}: {count}")


def print_validation_progress(provider: str, company: str, identifier: str):
    print(f"Validating {provider}: {company} ({identifier})...")


def run_search_workflow(app_config, limit: int = 20):
    result = run_job_search(app_config)

    print(f"\nMatched {len(result.jobs)} jobs")
    print(f"Saved {result.saved_count} new jobs to SQLite\n")

    print_search_diagnostics(result)
    print()

    print_jobs(result.jobs, limit)

    print("Generating report...")
    report = build_text_report(result.jobs, limit=limit)

    print("Saving report...")
    report_path = save_text_report(report)
    print(f"\nSaved report to {report_path}")

    if app_config.email.enabled:
        print("Sending email...")

    email_sent = send_report_email(
        report,
        app_config,
        subject=f"Auto-job report: {len(result.jobs)} matches",
    )

    if email_sent:
        print("Email sent")


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
def guide():
    """Show the recommended daily workflow."""

    print("\nRecommended workflow:\n")
    print("1. Validate configured sources")
    print("   python -m auto_job.cli validate-sources --problems-only")
    print("2. Discover new ATS sources from RSS jobs")
    print("   python -m auto_job.cli discover-from-rss --write")
    print("3. Run validation, search, storage, reporting, and email")
    print("   python -m auto_job.cli run")
    print("4. Review recently saved jobs")
    print("   python -m auto_job.cli recent")


@app.command()
def recent(limit: int = 10):
    """Show recent saved jobs."""

    jobs = get_recent_jobs(limit)

    print(f"\nShowing {len(jobs)} saved jobs:\n")

    print_jobs(jobs, limit)


@app.command()
def search(limit: int = 20):
    """Search enabled job sources, score results, and save matches."""
    app_config = load_config()

    run_search_workflow(app_config, limit=limit)


@app.command("validate-sources")
def validate_sources_command(problems_only: bool = False):
    """Validate configured job sources and print current job counts."""
    app_config = load_config()

    results = validate_sources(
        app_config,
        progress_callback=print_validation_progress,
    )
    print_source_validation_results(results, problems_only=problems_only)


@app.command()
def run(validate: bool = True, limit: int = 20):
    """Validate sources, run search, save report, and email if enabled."""
    app_config = load_config()

    if validate:
        results = validate_sources(
            app_config,
            progress_callback=print_validation_progress,
        )
        print_source_validation_results(results)

    run_search_workflow(app_config, limit=limit)


@app.command()
def detect_ats(url: str, write: bool = False):
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

    if write and result.company_slug:
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
def discover_ats(
    urls: list[str],
    write: bool = False,
    validate: bool = True,
):
    """Discover ATS providers from job or careers URLs."""
    results = discover_ats_from_job_urls(urls)

    if not results:
        print("No ATS providers discovered")
        return

    for result in results:
        print(f"\nDetected ATS: {result.provider}")
        print(f"ATS URL: {result.ats_url or 'Not found'}")
        print(f"Company slug: {result.company_slug or 'Not found'}")

        validation_result = None
        if validate:
            validation_result = validate_discovery_result(result)
            print(
                "Validation: "
                f"{validation_result.status}, {validation_result.job_count} jobs"
            )

        if write and result.company_slug:
            if validation_result and validation_result.status != "ok":
                print("Skipped invalid source")
                continue

            added = add_provider_source("config.yaml", result.provider, result.company_slug)

            if added:
                print("Added source to config.yaml")
            else:
                print("Source already exists or unsupported provider")



@app.command()
def discover_from_rss(write: bool = False, validate: bool = True):
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
    invalid_count = 0

    for result in results:
        print(f"\nDetected ATS: {result.provider}")
        print(f"ATS URL: {result.ats_url or 'Not found'}")
        print(f"Company slug: {result.company_slug or 'Not found'}")

        validation_result = None
        if validate:
            validation_result = validate_discovery_result(result)
            print(
                "Validation: "
                f"{validation_result.status}, {validation_result.job_count} jobs"
            )

        if write and result.company_slug:
            if validation_result and validation_result.status != "ok":
                invalid_count += 1
                print("Skipped invalid source")
                continue

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
        if validate:
            print(f"Skipped {invalid_count} invalid sources")



if __name__ == "__main__":
    app()
