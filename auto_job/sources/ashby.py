import httpx
import re

from auto_job.models import Job
from auto_job.sources.base import JobSource


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

            html = response.text

            html = html.replace("\\/", "/")
            html = html.replace("&quot;", '"')

            job_pattern = re.compile(
                r'"title":"([^"]+)".*?"id":"([a-f0-9-]{36})"',
                re.DOTALL,
            )

            matches = job_pattern.findall(html)

            for title, job_id in matches:
                posting_url = f"https://jobs.ashbyhq.com/{company_slug}/{job_id}"

                job = Job(
                    company=company,
                    title=title,
                    source="ashby",
                    posting_url=posting_url,
                    location="Unknown",
                    remote_status="unknown",
                    description="",
                )

                jobs.append(job)

        return jobs