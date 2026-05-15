# auto_job/job_search.py

from rich import print

from auto_job.sources.registry import SOURCE_REGISTRY
from auto_job.scoring import score_job
from auto_job.models import Job
from auto_job.storage import init_db, save_jobs
from auto_job.reporting import build_text_report, save_text_report
from dataclasses import dataclass


@dataclass
class JobSearchResult:
    jobs: list[Job]
    saved_count: int


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


def score_and_filter_jobs(jobs: list[Job], app_config,) -> list[Job]:
    """Score jobs and keep matches above minimum score."""
    matched_jobs = []

    for job in jobs:
        score = score_job(job, app_config)
        job.match_score = score

        if score >= app_config.filters.minimum_score:
            matched_jobs.append(job)

    return matched_jobs


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


def run_job_search(app_config) -> list[Job]:
    """Run the full job search pipeline."""
    jobs = fetch_jobs_from_sources(app_config)

    matched_jobs = score_and_filter_jobs(jobs, app_config)

    matched_jobs = dedupe_jobs(matched_jobs)

    matched_jobs.sort(
        key=lambda job: job.match_score,
        reverse=True
    )

    init_db()
    saved_count = save_jobs(matched_jobs)

    return JobSearchResult(
    jobs=matched_jobs,
    saved_count=saved_count,
    )