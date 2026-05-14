import feedparser

from auto_job.models import Job
from auto_job.sources.base import JobSource


class RSSSource(JobSource):
    name = "rss"

    def fetch_jobs(self) -> list[Job]:
        jobs: list[Job] = []

        for feed_config in self.config.sources.rss_feeds:
            feed = feedparser.parse(feed_config.url)

            for entry in feed.entries:
                try:
                    raw_title = entry.get("title", "Unknown")

                    if ":" in raw_title:
                        company, title = raw_title.split(":", 1)
                        company = company.strip()
                        title = title.strip()
                    else:
                        company = feed_config.name
                        title = raw_title

                    job = Job(
                        company=company,
                        title=title,
                        source=f"rss:{feed_config.name}",
                        posting_url=entry.get("link"),
                        location="Remote",
                        remote_status="remote",
                        description=entry.get("summary", ""),
                    )

                    jobs.append(job)

                except Exception as error:
                    print(f"Failed to parse RSS job: {error}")

        return jobs