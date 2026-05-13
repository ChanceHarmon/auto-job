import typer
from rich import print

from auto_job.config import load_config
from auto_job.models import Job
from auto_job.sources.demo import DemoSource
from auto_job.sources.remoteok import RemoteOKSource
from auto_job.filtering import job_matches_config
from auto_job.scoring import score_job

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

    print(f"\nFetched {len(jobs)} jobs from RemoteOK")
    print(f"Matched {len(scored_jobs)} jobs from your config\n")

    for job in scored_jobs[:10]:
        print(f"{job.match_score} | {job.title} @ {job.company}")
        print(job.posting_url)
        print(job.detected_stack)
        print()


if __name__ == "__main__":
    app()
