from auto_job.config import AppConfig
from auto_job.models import Job


def job_matches_config(job: Job, config: AppConfig) -> bool:
    searchable_text = " ".join(
        [
            job.title or "",
            job.company or "",
            job.location or "",
            job.description or "",
        ]
    ).lower()

    if config.search.remote_only and job.remote_status != "remote":
        return False

    if config.search.keywords:
        has_keyword_match = any(
            keyword.lower() in searchable_text
            for keyword in config.search.keywords
        )

        if not has_keyword_match:
            return False

    return True