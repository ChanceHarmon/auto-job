from dataclasses import dataclass
from rich import print

from auto_job.sources.registry import SOURCE_REGISTRY
from auto_job.scoring import score_job
from auto_job.models import Job
from auto_job.storage import init_db, save_jobs


@dataclass
class JobSearchResult:
    jobs: list[Job]
    saved_count: int
    source_fetch_counts: dict[str, int]
    source_match_counts: dict[str, int]
    filter_counts: dict[str, int]
    deduped_count: int


def get_source_key(job: Job) -> str:
    return job.source.split(":", 1)[0]


def fetch_jobs_from_sources(app_config) -> tuple[list[Job], dict[str, int]]:
    """Fetch jobs from all enabled sources."""
    all_jobs = []
    source_fetch_counts = {}

    for source_name in app_config.sources.enabled:
        print(f"Searching {source_name}...")
        source_fetch_counts[source_name] = 0

        source_class = SOURCE_REGISTRY.get(source_name)

        if source_class is None:
            print(f"Unknown source: {source_name}")
            continue

        source = source_class(app_config)
        jobs = source.fetch_jobs()

        print(f"Fetched {len(jobs)} jobs from {source_name}")

        source_fetch_counts[source_name] = len(jobs)
        all_jobs.extend(jobs)

    return all_jobs, source_fetch_counts


def get_filter_reason(job: Job, score: int, minimum_score: int) -> str:
    if score >= minimum_score:
        return ""

    if job.match_reasons:
        reason = job.match_reasons[0]

        if (
            reason.startswith("excluded keyword:")
            or reason in {"not remote", "outside allowed locations", "too old"}
        ):
            return reason

    return "below minimum score"


def score_and_filter_jobs(
    jobs: list[Job],
    app_config,
) -> tuple[list[Job], dict[str, int], dict[str, int]]:
    """Score jobs and keep matches above minimum score."""
    matched_jobs = []
    source_match_counts = {}
    filter_counts = {}

    for job in jobs:
        score = score_job(job, app_config)
        job.match_score = score

        if score >= app_config.filters.minimum_score:
            matched_jobs.append(job)
            source_key = get_source_key(job)
            source_match_counts[source_key] = source_match_counts.get(source_key, 0) + 1
        else:
            reason = get_filter_reason(
                job,
                score,
                app_config.filters.minimum_score,
            )
            filter_counts[reason] = filter_counts.get(reason, 0) + 1

    return matched_jobs, source_match_counts, filter_counts


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


def run_job_search(app_config) -> JobSearchResult:
    """Run the full job search pipeline."""
    jobs, source_fetch_counts = fetch_jobs_from_sources(app_config)

    matched_jobs, source_match_counts, filter_counts = score_and_filter_jobs(jobs, app_config)

    matched_jobs = dedupe_jobs(matched_jobs)
    deduped_count = sum(source_match_counts.values()) - len(matched_jobs)

    matched_jobs.sort(
        key=lambda job: job.match_score,
        reverse=True
    )

    init_db()
    saved_count = save_jobs(matched_jobs)

    return JobSearchResult(
        jobs=matched_jobs,
        saved_count=saved_count,
        source_fetch_counts=source_fetch_counts,
        source_match_counts=source_match_counts,
        filter_counts=filter_counts,
        deduped_count=deduped_count,
    )
