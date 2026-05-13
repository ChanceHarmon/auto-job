import httpx

from auto_job.models import Job
from auto_job.sources.base import JobSource


class RemoteOKSource(JobSource):
    name = "remoteok"

    API_URL = "https://remoteok.com/api"

    def fetch_jobs(self) -> list[Job]:
        response = httpx.get(
            self.API_URL,
            headers={
                "User-Agent": "auto-job/0.1"
            }
        )

        response.raise_for_status()

        raw_jobs = response.json()

        jobs: list[Job] = []

        for raw_job in raw_jobs[1:]:
            try:
                job = Job(
                    company=raw_job.get("company", "Unknown"),
                    title=raw_job.get("position", "Unknown"),
                    source=self.name,
                    posting_url=raw_job.get("url"),
                    location=raw_job.get("location"),
                    remote_status="remote",
                    description=raw_job.get("description")
                )

                jobs.append(job)

            except Exception as error:
                print(f"Failed to parse job: {error}")

        return jobs