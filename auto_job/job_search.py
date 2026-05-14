# auto_job/job_search.py

from rich import print

from auto_job.sources.registry import SOURCE_REGISTRY
from auto_job.scoring import score_job


def fetch_jobs_from_sources(app_config):
    """Fetch jobs from all enabled sources."""
    all_jobs = []

    for source_name in app_config.sources.enabled:
        print(f"Searching {source_name}...")

        source_class = SOURCE_REGISTRY.get(source_name)

        if source_class is None:
            print(f"Unknown source: {source_name}")
            continue

        source = source_class(app_config)
        jobs = source.fetch_jobs()

        print(f"Fetched {len(jobs)} jobs from {source_name}")

        all_jobs.extend(jobs)

    return all_jobs


def score_and_filter_jobs(jobs, app_config):
    """Score jobs and keep matches above minimum score."""
    matched_jobs = []

    for job in jobs:
        score = score_job(job, app_config)
        job.match_score = score

        if score >= app_config.filters.minimum_score:
            matched_jobs.append(job)

    return matched_jobs