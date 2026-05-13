from auto_job.config import AppConfig
from auto_job.models import Job


def score_job(job: Job, config: AppConfig) -> int:
    score = 0
    reasons = []

    searchable_text = " ".join(
        [
            job.title or "",
            job.company or "",
            job.location or "",
            job.description or "",
        ]
    ).lower()

    # Keyword matches
    # Keyword matches
    for keyword in config.search.keywords:
        keyword_parts = keyword.lower().split()

        matches = sum(
            1
            for part in keyword_parts
            if part in searchable_text
        )

        score += matches * 10
        reasons.append(f"keyword match: {keyword}")

        title_matches = sum(
            1
            for part in keyword_parts
            if part in job.title.lower()
        )

        score += title_matches * 10
        reasons.append(f"title match: {keyword}")

    # Preferred stack matches
    for tech in config.filters.preferred_stack:
        if tech.lower() in searchable_text:
            score += 5
            reasons.append(f"preferred stack: {tech}")

    # Remote boost
    if job.remote_status == "remote":
        score += 10

    # Excluded keyword penalties
    for excluded in config.filters.excluded_keywords:
        if excluded.lower() in searchable_text:
            score -= 25
            reasons.append(f"excluded keyword: {excluded}")

    job.detected_stack = reasons
    return score