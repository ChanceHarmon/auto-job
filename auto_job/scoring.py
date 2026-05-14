from auto_job.config import AppConfig
from auto_job.models import Job
from datetime import date, timedelta


def score_job(job: Job, config: AppConfig) -> int:
    score = 0
    reasons = []

    searchable_text = " ".join(
        [
            job.title or "",
            job.company or "",
            job.location or "",
            job.remote_status or "",
            job.description or "",
        ]
    ).lower()

    # Hard exclude unwanted jobs before scoring
    for excluded in config.filters.excluded_keywords:
        if excluded.lower() in searchable_text:
            job.match_score = 0
            job.detected_stack = [f"excluded keyword: {excluded}"]
            return 0

    # Hard exclude non-remote jobs when remote_only is enabled
    if config.search.remote_only and job.remote_status != "remote":
        job.match_score = 0
        job.detected_stack = ["not remote"]
        return 0
    
        # Hard exclude old jobs
    if job.date_posted:
        cutoff_date = date.today() - timedelta(days=config.search.recency_days)

        if job.date_posted < cutoff_date:
            job.match_score = 0
            job.detected_stack = ["too old"]
            return 0
    
    # Keyword matches
    for keyword in config.search.keywords:
        keyword_parts = keyword.lower().split()

        matches = sum(
            1
            for part in keyword_parts
            if part in searchable_text
        )

        if matches > 0:
            score += matches * 10
            reasons.append(f"keyword match: {keyword}")

        title_matches = sum(
            1
            for part in keyword_parts
            if part in job.title.lower()
        )

        if title_matches > 0:
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
        reasons.append("remote")

    job.match_score = score
    job.detected_stack = reasons

    return score