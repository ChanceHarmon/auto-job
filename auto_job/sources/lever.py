import httpx

from auto_job.models import Job
from auto_job.sources.base import JobSource


class LeverSource(JobSource):

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

            except Exception as error:
                print(
                    f"Error fetching Lever jobs "
                    f"for {company_slug}: {error}"
                )

                continue

            for posting in postings:

                categories = posting.get("categories", {})

                location = categories.get(
                    "location",
                    "Unknown",
                )

                remote_status = (
                    "remote"
                    if "remote" in location.lower()
                    else "onsite"
                )

                job = Job(
                    company=company,
                    title=posting.get("text", "Unknown title"),
                    source="lever",
                    posting_url=posting.get("hostedUrl"),
                    location=location,
                    remote_status=remote_status,
                    description=posting.get(
                        "descriptionPlain",
                        "",
                    ),
                )

                jobs.append(job)

        return jobs