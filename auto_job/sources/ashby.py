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

            html = (
                response.text
                .replace("\\/", "/")
                .replace("&quot;", '"')
            )

            matches = JOB_PATTERN.findall(html)

            for job_id, title, location, workplace_type, published_date in matches:
                remote_status = (
                    "remote"
                    if workplace_type.lower() == "remote"
                    else "onsite"
                )

                posting_url = f"https://jobs.ashbyhq.com/{company_slug}/{job_id}"

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