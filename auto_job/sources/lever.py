from datetime import date, datetime, timezone
from html import escape

import httpx

from auto_job.description_utils import clean_description
from auto_job.models import Job
from auto_job.sources.base import JobSource


def parse_lever_date(created_at: int | None) -> date | None:
    if not created_at:
        return None

    return datetime.fromtimestamp(created_at / 1000, timezone.utc).date()


def detect_lever_remote_status(location: str | None) -> str:
    if not location:
        return "unknown"

    if "remote" in location.lower():
        return "remote"

    return "onsite"


def build_lever_description(posting: dict) -> str:
    """Combine Lever's split description/list fields into one reportable body."""
    description_parts = []

    description_plain = posting.get("descriptionPlain")

    if description_plain:
        description_parts.append(description_plain)

    content = posting.get("content") or {}

    description = content.get("description")

    if description and description not in description_parts:
        description_parts.append(description)

    for section in content.get("lists", []):
        section_title = section.get("text")
        section_content = section.get("content")

        if section_title:
            description_parts.append(section_title)

        if section_content:
            description_parts.append(section_content)

    closing = content.get("closing")

    if closing:
        description_parts.append(closing)

    return clean_description("\n\n".join(description_parts))


def build_lever_description_html(posting: dict) -> str:
    content = posting.get("content") or {}
    description_parts = []

    description = content.get("description")

    if description:
        description_parts.append(description)

    for section in content.get("lists", []):
        section_title = section.get("text")
        section_content = section.get("content")

        if section_title:
            description_parts.append(f"<h3>{escape(section_title)}</h3>")

        if section_content:
            description_parts.append(section_content)

    closing = content.get("closing")

    if closing:
        description_parts.append(closing)

    if description_parts:
        return "\n\n".join(description_parts)

    return posting.get("description") or ""


def normalize_lever_posting(company: str, posting: dict) -> Job:
    """Convert one Lever posting response into the shared Job model."""
    categories = posting.get("categories") or {}
    location = categories.get("location")

    return Job(
        company=company,
        title=posting.get("text") or "Unknown title",
        source=LeverSource.name,
        posting_url=posting.get("hostedUrl") or posting.get("applyUrl"),
        location=location,
        remote_status=detect_lever_remote_status(location),
        date_posted=parse_lever_date(posting.get("createdAt")),
        description=build_lever_description(posting),
        description_html=build_lever_description_html(posting),
    )


class LeverSource(JobSource):
    """Fetch and normalize jobs from configured Lever company slugs."""

    name = "lever"

    def fetch_jobs(self) -> list[Job]:
        jobs = []

        lever_companies = getattr(
            self.config.sources,
            "lever_companies",
            [],
        )

        for company_config in lever_companies:
            company = company_config.company
            company_slug = company_config.company_slug

            url = (
                f"https://api.lever.co/v0/postings/"
                f"{company_slug}?mode=json"
            )

            try:
                response = httpx.get(
                    url,
                    timeout=10,
                )

                response.raise_for_status()

                postings = response.json()

            except httpx.HTTPStatusError as error:
                if error.response.status_code == 404:
                    print(
                        f"Skipping Lever company {company_slug}: "
                        "not found. Check the company_slug or confirm the company still uses Lever."
                    )
                else:
                    print(
                        f"Error fetching Lever jobs "
                        f"for {company_slug}: {error}"
                    )

                continue

            except httpx.RequestError as error:
                print(
                    f"Error fetching Lever jobs "
                    f"for {company_slug}: {error}"
                )

                continue

            for posting in postings:
                job = normalize_lever_posting(company, posting)

                jobs.append(job)

        return jobs
