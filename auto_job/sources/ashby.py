import httpx
import re

from auto_job.models import Job
from auto_job.sources.base import JobSource

JOB_PATTERN = re.compile(
    r'"id":"([a-f0-9-]{36})".*?'
    r'"title":"([^"]+)".*?'
    r'"locationName":"([^"]*)".*?'
    r'"workplaceType":"([^"]*)".*?'
    r'"publishedDate":"([^"]*)"',
    re.DOTALL,
)

def clean_ashby_html(html: str) -> str:
    return html.replace("\\/", "/").replace("&quot;", '"')


def parse_ashby_jobs(html: str) -> list[tuple[str, str, str, str, str]]:
    clean_html = clean_ashby_html(html)
    return JOB_PATTERN.findall(clean_html)


def get_remote_status(workplace_type: str) -> str:
    if workplace_type.lower() == "remote":
        return "remote"

    return "onsite"


def build_ashby_posting_url(company_slug: str, job_id: str) -> str:
    return f"https://jobs.ashbyhq.com/{company_slug}/{job_id}"

class AshbySource(JobSource):

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

            for job_id, title, location, workplace_type, published_date in matches:
                remote_status = get_remote_status(workplace_type)

                posting_url = build_ashby_posting_url(company_slug, job_id)

                job = Job(
                    company=company,
                    title=title,
                    source="ashby",
                    posting_url=posting_url,
                    location=location,
                    remote_status=remote_status,
                    date_posted=published_date,
                    description="",
                )
                jobs.append(job)

        return jobs