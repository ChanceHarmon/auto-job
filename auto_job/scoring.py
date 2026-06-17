from auto_job.config import AppConfig
from auto_job.models import Job
from datetime import date, timedelta


US_LOCATION_TERMS = {
    "united states",
    "usa",
    "u.s.",
    "u.s.a.",
    "us-remote",
    "us remote",
    "remote in us",
    "remote - us",
    "remote, us",
    "united states - remote",
    "california",
    "colorado",
    "oregon",
    "washington",
    "new york",
    "texas",
    "illinois",
    "florida",
    "massachusetts",
    "san francisco",
    "seattle",
    "chicago",
    "austin",
    "boston",
    "denver",
}

CANADA_LOCATION_TERMS = {
    "canada",
    "can-remote",
    "can remote",
    "remote - canada",
    "remote, canada",
    "toronto",
    "vancouver",
    "ontario",
    "british columbia",
}

IGNORED_LOCATION_TERMS = {"remote"}


def get_allowed_location_terms(config: AppConfig) -> set[str]:
    configured_terms = {
        location.lower().strip()
        for location in config.search.locations
        if location.lower().strip() not in IGNORED_LOCATION_TERMS
    }

    allowed_terms = set(configured_terms)

    if "united states" in configured_terms or "usa" in configured_terms:
        allowed_terms.update(US_LOCATION_TERMS)

    if "canada" in configured_terms:
        allowed_terms.update(CANADA_LOCATION_TERMS)

    if "north america" in configured_terms:
        allowed_terms.update(US_LOCATION_TERMS)
        allowed_terms.update(CANADA_LOCATION_TERMS)
        allowed_terms.add("north america")

    return allowed_terms


def location_is_allowed(job: Job, config: AppConfig) -> bool:
    allowed_terms = get_allowed_location_terms(config)

    if not allowed_terms:
        return True

    if not job.location:
        return True

    location_text = job.location.lower()

    return any(term in location_text for term in allowed_terms)


def score_job(job: Job, config: AppConfig) -> int:
    score = 0
    reasons = []
    detected_stack = []

    searchable_text = " ".join(
        [
            job.title or "",
            job.company or "",
            job.location or "",
            job.remote_status or "",
            job.description or "",
        ]
    ).lower()
    title_text = (job.title or "").lower()

    # Hard exclude unwanted job titles before scoring
    for excluded in config.filters.excluded_keywords:
        if excluded.lower() in title_text:
            job.match_score = 0
            job.match_reasons = [f"excluded keyword: {excluded}"]
            return 0

    # Hard exclude non-remote jobs when remote_only is enabled
    if config.search.remote_only and job.remote_status != "remote":
        job.match_score = 0
        job.match_reasons = ["not remote"]
        return 0

    # Hard exclude jobs outside configured locations
    if not location_is_allowed(job, config):
        job.match_score = 0
        job.match_reasons = ["outside allowed locations"]
        return 0

    # Hard exclude old jobs
    if job.date_posted:
        cutoff_date = date.today() - timedelta(days=config.search.recency_days)

        if job.date_posted < cutoff_date:
            job.match_score = 0
            job.match_reasons = ["too old"]
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
            detected_stack.append(tech)
            reasons.append(f"preferred stack: {tech}")

    # Remote boost
    if job.remote_status == "remote":
        score += 10
        reasons.append("remote")

    job.match_score = score
    job.detected_stack = detected_stack
    job.match_reasons = reasons

    return score
