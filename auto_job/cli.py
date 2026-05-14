import typer
from rich import print

from auto_job.config import load_config
from auto_job.models import Job
from auto_job.sources.demo import DemoSource
from auto_job.sources.remoteok import RemoteOKSource
from auto_job.scoring import score_job
from auto_job.storage import init_db, save_jobs
from auto_job.storage import get_recent_jobs
from auto_job.sources.registry import SOURCE_REGISTRY

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
def remoteok():
    """Fetch and score matching jobs from RemoteOK."""
    app_config = load_config()

    source = RemoteOKSource(app_config)
    jobs = source.fetch_jobs()

    scored_jobs = []

    for job in jobs:
        score = score_job(job, app_config)
        job.match_score = score

        if score > 0:
            scored_jobs.append(job)

    scored_jobs.sort(
        key=lambda job: job.match_score,
        reverse=True
    )

    init_db()
    saved_count = save_jobs(scored_jobs)

    print(f"\nFetched {len(jobs)} jobs from RemoteOK")
    print(f"Matched {len(scored_jobs)} jobs from your config\n")
    print(f"Saved {saved_count} new jobs to SQLite\n")

    for job in scored_jobs[:10]:
        print(f"{job.match_score} | {job.title} @ {job.company}")
        print(job.posting_url)
        print(job.detected_stack)
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

    all_scored_jobs = []

    for source_name in app_config.sources.enabled:
        print(f"Searching {source_name}...")

        source_class = SOURCE_REGISTRY.get(source_name)

        if source_class is None:
            print(f"Unknown source: {source_name}")
            continue

        source = source_class(app_config)
        jobs = source.fetch_jobs()

        print(f"Fetched {len(jobs)} jobs from {source_name}")

        for job in jobs:
            score = score_job(job, app_config)
            job.match_score = score
            # print(f"{score} | {job.title} @ {job.company} ({job.source})")

            if score >= app_config.filters.minimum_score:
                all_scored_jobs.append(job)

    all_scored_jobs = dedupe_jobs(all_scored_jobs)

    all_scored_jobs.sort(
        key=lambda job: job.match_score,
        reverse=True
    )

    init_db()
    saved_count = save_jobs(all_scored_jobs)

    print(f"\nMatched {len(all_scored_jobs)} jobs")
    print(f"Saved {saved_count} new jobs to SQLite\n")

    print_jobs(all_scored_jobs, 10)



if __name__ == "__main__":
    app()
