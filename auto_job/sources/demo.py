from auto_job.models import Job
from auto_job.sources.base import JobSource


class DemoSource(JobSource):
    name = "demo"

    def fetch_jobs(self) -> list[Job]:
        return [
            Job(
                company="Example Co",
                title="Backend Engineer",
                source=self.name,
                posting_url="https://example.com/backend",
                location="Remote",
                remote_status="remote",
                description="Python, APIs, PostgreSQL"
            ),
            Job(
                company="Another Company",
                title="Full Stack Developer",
                source=self.name,
                posting_url="https://example.com/fullstack",
                location="United States",
                remote_status="hybrid",
                description="React, TypeScript, Node"
            )
        ]