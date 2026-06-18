from concurrent.futures import ThreadPoolExecutor

import httpx
import json
import re

from auto_job.models import Job
from auto_job.sources.base import JobSource

JOB_ID_PATTERN = re.compile(r'"id":"([a-f0-9-]{36})"')
JOB_FIELD_PATTERNS = {
    "title": re.compile(r'"title":"([^"]+)"'),
    "location": re.compile(r'"locationName":"([^"]*)"'),
    "workplace_type": re.compile(r'"workplaceType":"([^"]*)"'),
    "published_date": re.compile(r'"publishedDate":"([^"]*)"'),
}
JOB_PARSE_WINDOW = 5000

JSON_LD_PATTERN = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>',
    re.DOTALL,
)
META_DESCRIPTION_PATTERN = re.compile(
    r'<meta name="description" content="([^"]*)"',
    re.DOTALL,
)
MAX_DESCRIPTION_WORKERS = 8


def clean_ashby_html(html: str) -> str:
    """Undo common escaping in Ashby's embedded page data."""
    return html.replace("\\/", "/").replace("&quot;", '"')


def parse_ashby_jobs(html: str) -> list[tuple[str, str, str, str, str]]:
    """Extract listing data from Ashby's rendered careers page HTML."""
    clean_html = clean_ashby_html(html)
    jobs = []

    for id_match in JOB_ID_PATTERN.finditer(clean_html):
        # Keep parsing bounded around each id. A single cross-document regex can
        # get very slow on large or nonstandard Ashby pages that do not contain
        # the expected fields in order.
        job_window = clean_html[
            id_match.start():id_match.start() + JOB_PARSE_WINDOW
        ]
        field_matches = {
            field: pattern.search(job_window)
            for field, pattern in JOB_FIELD_PATTERNS.items()
        }

        if not all(field_matches.values()):
            continue

        jobs.append(
            (
                id_match.group(1),
                field_matches["title"].group(1),
                field_matches["location"].group(1),
                field_matches["workplace_type"].group(1),
                field_matches["published_date"].group(1),
            )
        )

    return jobs


def parse_ashby_description(html: str) -> str:
    """Prefer JSON-LD job descriptions, falling back to meta description text."""
    match = JSON_LD_PATTERN.search(html)

    if match:
        try:
            job_data = json.loads(match.group(1))
        except json.JSONDecodeError:
            job_data = {}

        description = job_data.get("description")

        if description:
            return description

    meta_match = META_DESCRIPTION_PATTERN.search(html)

    if meta_match:
        return meta_match.group(1)

    return ""


def get_remote_status(workplace_type: str) -> str:
    if workplace_type.lower() == "remote":
        return "remote"

    return "onsite"


def build_ashby_posting_url(company_slug: str, job_id: str) -> str:
    return f"https://jobs.ashbyhq.com/{company_slug}/{job_id}"


def fetch_ashby_description(posting_url: str) -> str:
    try:
        response = httpx.get(posting_url, timeout=10)
        response.raise_for_status()
    except Exception as error:
        print(f"Error fetching Ashby job description for {posting_url}: {error}")
        return ""

    return parse_ashby_description(response.text)


def fetch_ashby_descriptions(posting_urls: list[str]) -> dict[str, str]:
    """Fetch individual posting descriptions concurrently for one Ashby board."""
    if not posting_urls:
        return {}

    worker_count = min(MAX_DESCRIPTION_WORKERS, len(posting_urls))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        descriptions = executor.map(fetch_ashby_description, posting_urls)

    return dict(zip(posting_urls, descriptions))


class AshbySource(JobSource):
    """Fetch Ashby listings and enrich them with per-posting descriptions."""

    name = "ashby"

    def fetch_jobs(self) -> list[Job]:
        jobs = []

        ashby_companies = getattr(
            self.config.sources,
            "ashby_companies",
            [],
        )

        for company_config in ashby_companies:
            company = company_config.company
            company_slug = company_config.company_slug

            url = f"https://jobs.ashbyhq.com/{company_slug}"

            try:
                response = httpx.get(url, timeout=10)
                response.raise_for_status()
            except Exception as error:
                print(f"Error fetching Ashby jobs for {company_slug}: {error}")
                continue

            matches = parse_ashby_jobs(response.text)
            posting_urls = [
                build_ashby_posting_url(company_slug, job_id)
                for job_id, _, _, _, _ in matches
            ]
            # The board page has listing metadata, while richer descriptions
            # live on individual posting pages.
            descriptions_by_url = fetch_ashby_descriptions(posting_urls)

            for job_id, title, location, workplace_type, published_date in matches:
                remote_status = get_remote_status(workplace_type)

                posting_url = build_ashby_posting_url(company_slug, job_id)
                description = descriptions_by_url.get(posting_url, "")

                job = Job(
                    company=company,
                    title=title,
                    source="ashby",
                    posting_url=posting_url,
                    location=location,
                    remote_status=remote_status,
                    date_posted=published_date,
                    description=description,
                )
                jobs.append(job)

        return jobs
