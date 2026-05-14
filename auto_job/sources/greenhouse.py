import httpx
from datetime import datetime

from auto_job.models import Job
from auto_job.sources.base import JobSource


class GreenhouseSource(JobSource):
    name = "greenhouse"

    API_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    def detect_remote_status(self, location: str | None) -> str:
        if not location:
            return "unknown"

        location_lower = location.lower()

        if "remote" in location_lower:
            return "remote"

        return "onsite"


    def fetch_jobs(self) -> list[Job]:
        jobs: list[Job] = []

        for board in self.config.sources.greenhouse_boards:
            url = self.API_URL.format(board_token=board.board_token)

            try:
                response = httpx.get(
                    url,
                    headers={
                        "User-Agent": "auto-job/0.1"
                    },
                    timeout=10.0,
                )

                response.raise_for_status()

            except httpx.HTTPStatusError as error:
                print(
                    f"Skipping Greenhouse board: {board.company} "
                    f"({board.board_token}) - {error.response.status_code}"
                )
                continue

            except httpx.RequestError as error:
                print(
                    f"Skipping Greenhouse board: {board.company} "
                    f"({board.board_token}) - request failed: {error}"
                )
                continue

            raw_data = response.json()

            for raw_job in raw_data.get("jobs", []):
                try:
                    location = raw_job.get("location") or {}
                    location_name = location.get("name")
                    remote_status = self.detect_remote_status(location_name)

                    updated_at = raw_job.get("updated_at")

                    date_posted = None

                    if updated_at:
                        date_posted = datetime.fromisoformat(updated_at).date()

                    job = Job(
                        company=board.company,
                        title=raw_job.get("title", "Unknown"),
                        source=self.name,
                        posting_url=raw_job.get("absolute_url"),
                        location=location_name,
                        remote_status=remote_status,
                        salary=None,
                        date_posted=date_posted,
                        description=raw_job.get("content", ""),
                    )

                    jobs.append(job)

                except Exception as error:
                    print(f"Failed to parse Greenhouse job: {error}")

        return jobs