from datetime import date, timedelta
import re

from auto_job.config import AppConfig
from auto_job.models import Job


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
TITLE_PENALTY_POINTS = 20
PREFERRED_TITLE_POINTS = 20


def title_keyword_variants(keyword: str) -> list[str]:
    """Return title matching aliases for common job-board abbreviations."""
    normalized_keyword = keyword.lower().strip()

    if normalized_keyword == "senior":
        return ["senior", "sr"]

    return [normalized_keyword]


def title_matches_keyword(title_text: str, keyword: str) -> bool:
    """Match title filters safely, especially short words like IT, ML, or Sr.

    Longer phrases keep simple substring behavior because that works well for
    terms like "machine learning". Short terms use token boundaries so "it"
    does not match inside unrelated words.
    """
    for variant in title_keyword_variants(keyword):
        compact_variant = re.sub(r"[^a-z0-9]", "", variant)

        if len(compact_variant) <= 3:
            pattern = rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])"

            if re.search(pattern, title_text):
                return True

            continue

        if variant in title_text:
            return True

    return False


def get_allowed_location_terms(config: AppConfig) -> set[str]:
    """Expand user-facing location config into provider-specific match terms."""
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
    """Return whether a job's location falls inside the configured geography."""
    allowed_terms = get_allowed_location_terms(config)

    if not allowed_terms:
        return True

    if not job.location:
        return True

    location_text = job.location.lower()

    return any(term in location_text for term in allowed_terms)


def score_job(job: Job, config: AppConfig) -> int:
    """Score one normalized job and annotate it with match details.

    The order matters: hard filters return immediately, then positive boosts
    and penalties build a transparent score that can be shown in reports.
    """
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

    # Hard filters remove jobs that should never appear in the final report.
    for excluded in config.filters.excluded_keywords:
        if title_matches_keyword(title_text, excluded):
            job.match_score = 0
            job.match_reasons = [f"excluded keyword: {excluded}"]
            return 0

    if config.search.remote_only and job.remote_status != "remote":
        job.match_score = 0
        job.match_reasons = ["not remote"]
        return 0

    if not location_is_allowed(job, config):
        job.match_score = 0
        job.match_reasons = ["outside allowed locations"]
        return 0

    if job.date_posted:
        cutoff_date = date.today() - timedelta(days=config.search.recency_days)

        if job.date_posted < cutoff_date:
            job.match_score = 0
            job.match_reasons = ["too old"]
            return 0

    # Configured keywords represent broad search intent and count in both
    # full posting text and title text.
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

    # Stack/title preferences and penalties tune ranking without changing the
    # hard-filter behavior.
    for tech in config.filters.preferred_stack:
        if tech.lower() in searchable_text:
            score += 5
            detected_stack.append(tech)
            reasons.append(f"preferred stack: {tech}")

    for preferred_title in config.filters.preferred_titles:
        if title_matches_keyword(title_text, preferred_title):
            score += PREFERRED_TITLE_POINTS
            reasons.append(f"preferred title: {preferred_title}")

    for penalty_keyword in config.filters.penalty_keywords:
        if title_matches_keyword(title_text, penalty_keyword):
            score -= TITLE_PENALTY_POINTS
            reasons.append(f"title penalty: {penalty_keyword}")

    # Remote boost
    if job.remote_status == "remote":
        score += 10
        reasons.append("remote")

    job.match_score = score
    job.detected_stack = detected_stack
    job.match_reasons = reasons

    return score
