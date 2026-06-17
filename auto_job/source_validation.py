from dataclasses import dataclass

import feedparser
import httpx

from auto_job.ats import AtsDetectionResult
from auto_job.config import (
    AppConfig,
    AshbyCompanyConfig,
    GreenhouseBoardConfig,
    LeverCompanyConfig,
)
from auto_job.sources.ashby import parse_ashby_jobs


@dataclass
class SourceValidationResult:
    provider: str
    company: str
    identifier: str
    status: str
    job_count: int = 0
    message: str = ""


def validate_discovery_result(result: AtsDetectionResult) -> SourceValidationResult:
    if not result.company_slug:
        return SourceValidationResult(
            provider=result.provider,
            company="Unknown",
            identifier="",
            status="error",
            message="missing company slug",
        )

    company = result.company_slug.title()

    if result.provider == "greenhouse":
        return validate_greenhouse_board(
            GreenhouseBoardConfig(
                company=company,
                board_token=result.company_slug,
            )
        )

    if result.provider == "lever":
        return validate_lever_company(
            LeverCompanyConfig(
                company=company,
                company_slug=result.company_slug,
            )
        )

    if result.provider == "ashby":
        return validate_ashby_company(
            AshbyCompanyConfig(
                company=company,
                company_slug=result.company_slug,
            )
        )

    return SourceValidationResult(
        provider=result.provider,
        company=company,
        identifier=result.company_slug,
        status="error",
        message="unsupported provider",
    )


def validate_rss_feed(feed_config) -> SourceValidationResult:
    feed = feedparser.parse(feed_config.url)
    job_count = len(feed.entries)

    status = "ok" if job_count else "empty"

    if feed.bozo:
        status = "error"

    return SourceValidationResult(
        provider="rss",
        company=feed_config.name,
        identifier=feed_config.url,
        status=status,
        job_count=job_count,
        message=str(feed.bozo_exception) if feed.bozo else "",
    )


def validate_greenhouse_board(board_config) -> SourceValidationResult:
    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        f"{board_config.board_token}/jobs?content=false"
    )

    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        return SourceValidationResult(
            provider="greenhouse",
            company=board_config.company,
            identifier=board_config.board_token,
            status="error",
            message=f"HTTP {error.response.status_code}",
        )
    except httpx.RequestError as error:
        return SourceValidationResult(
            provider="greenhouse",
            company=board_config.company,
            identifier=board_config.board_token,
            status="error",
            message=str(error),
        )

    jobs = response.json().get("jobs", [])

    return SourceValidationResult(
        provider="greenhouse",
        company=board_config.company,
        identifier=board_config.board_token,
        status="ok" if jobs else "empty",
        job_count=len(jobs),
    )


def validate_lever_company(company_config) -> SourceValidationResult:
    url = f"https://api.lever.co/v0/postings/{company_config.company_slug}?mode=json"

    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        return SourceValidationResult(
            provider="lever",
            company=company_config.company,
            identifier=company_config.company_slug,
            status="error",
            message=f"HTTP {error.response.status_code}",
        )
    except httpx.RequestError as error:
        return SourceValidationResult(
            provider="lever",
            company=company_config.company,
            identifier=company_config.company_slug,
            status="error",
            message=str(error),
        )

    jobs = response.json()

    return SourceValidationResult(
        provider="lever",
        company=company_config.company,
        identifier=company_config.company_slug,
        status="ok" if jobs else "empty",
        job_count=len(jobs),
    )


def validate_ashby_company(company_config) -> SourceValidationResult:
    url = f"https://jobs.ashbyhq.com/{company_config.company_slug}"

    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        return SourceValidationResult(
            provider="ashby",
            company=company_config.company,
            identifier=company_config.company_slug,
            status="error",
            message=f"HTTP {error.response.status_code}",
        )
    except httpx.RequestError as error:
        return SourceValidationResult(
            provider="ashby",
            company=company_config.company,
            identifier=company_config.company_slug,
            status="error",
            message=str(error),
        )

    jobs = parse_ashby_jobs(response.text)

    return SourceValidationResult(
        provider="ashby",
        company=company_config.company,
        identifier=company_config.company_slug,
        status="ok" if jobs else "empty",
        job_count=len(jobs),
    )


def validate_sources(app_config: AppConfig, progress_callback=None) -> list[SourceValidationResult]:
    results = []

    for feed_config in app_config.sources.rss_feeds:
        if progress_callback:
            progress_callback("rss", feed_config.name, feed_config.url)

        results.append(validate_rss_feed(feed_config))

    for board_config in app_config.sources.greenhouse_boards:
        if progress_callback:
            progress_callback("greenhouse", board_config.company, board_config.board_token)

        results.append(validate_greenhouse_board(board_config))

    for company_config in app_config.sources.lever_companies:
        if progress_callback:
            progress_callback("lever", company_config.company, company_config.company_slug)

        results.append(validate_lever_company(company_config))

    for company_config in app_config.sources.ashby_companies:
        if progress_callback:
            progress_callback("ashby", company_config.company, company_config.company_slug)

        results.append(validate_ashby_company(company_config))

    return results
