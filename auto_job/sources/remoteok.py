from datetime import date, datetime

import httpx

from auto_job.models import Job
from auto_job.sources.base import JobSource


def parse_remoteok_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def format_remoteok_salary(raw_job: dict) -> str | None:
    salary_min = raw_job.get("salary_min") or 0
    salary_max = raw_job.get("salary_max") or 0

    if not salary_min and not salary_max:
        return None

    if salary_min and salary_max:
        return f"${salary_min:,} - ${salary_max:,}"

    if salary_min:
        return f"${salary_min:,}+"

    return f"Up to ${salary_max:,}"


def build_remoteok_description(raw_job: dict) -> str:
    description = raw_job.get("description") or ""
    tags = raw_job.get("tags") or []

    if not tags:
        return description

    return f"{description}\n\nTags: {', '.join(tags)}"


def normalize_remoteok_job(raw_job: dict) -> Job:
    """Convert one RemoteOK API row into the shared Job model."""
    return Job(
        company=raw_job.get("company") or "Unknown",
        title=raw_job.get("position") or "Unknown",
        source=RemoteOKSource.name,
        posting_url=raw_job.get("url") or raw_job.get("apply_url"),
        location=raw_job.get("location") or None,
        remote_status="remote",
        salary=format_remoteok_salary(raw_job),
        date_posted=parse_remoteok_date(raw_job.get("date")),
        description=build_remoteok_description(raw_job),
    )


class RemoteOKSource(JobSource):
    """Fetch and normalize jobs from RemoteOK's public API."""

    name = "remoteok"

    API_URL = "https://remoteok.com/api"

    def fetch_jobs(self) -> list[Job]:
        response = httpx.get(
            self.API_URL,
            headers={
                "User-Agent": "auto-job/0.1"
            },
            timeout=10,
        )

        response.raise_for_status()

        raw_jobs = response.json()

        jobs: list[Job] = []

        # RemoteOK's first response row is API metadata, not an actual job.
        for raw_job in raw_jobs[1:]:
            try:
                job = normalize_remoteok_job(raw_job)

                jobs.append(job)

            except Exception as error:
                print(f"Failed to parse job: {error}")

        return jobs
